"""Provider abstraction with Gemini-first and Grok fallback support."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterable

from lighted_ai.config import get_api_key, get_grok_api_key, settings
from lighted_ai.gemini_client import GeminiClient


class ProviderError(RuntimeError):
    """Raised when a provider cannot complete a request."""


class ProviderFallbackError(RuntimeError):
    """Raised when all configured providers fail."""


class GroqClient:
    """Minimal Groq client compatible with the OpenAI-style chat completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        timeout_seconds: float = 60.0,
        base_url: str = "https://api.groq.com/openai/v1/chat/completions",
    ) -> None:
        key = api_key if api_key is not None else get_grok_api_key()
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Groq API key is not configured.")

        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive.")

        selected_model = model if model is not None else settings.groq_model
        if not isinstance(selected_model, str) or not selected_model.strip():
            raise ValueError("groq_model must be a non-empty string.")

        self.api_key = key.strip()
        self.model_name = selected_model.strip()
        self.timeout_seconds = float(timeout_seconds)
        self.endpoint = base_url

    def generate(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> str:
        return self.generate_text(prompt, system=system, **kwargs)

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float | None = 0.2,
        response_mime_type: str | None = None,
        system: str | None = None,
    ) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string.")

        if system is not None and not isinstance(system, str):
            raise TypeError("system must be a string or None.")

        if temperature is not None:
            if (
                isinstance(temperature, bool)
                or not isinstance(temperature, (int, float))
                or not 0.0 <= float(temperature) <= 2.0
            ):
                raise ValueError("temperature must be between 0 and 2.")

        messages: list[dict[str, str]] = []
        if system and system.strip():
            messages.append({"role": "system", "content": system.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": float(temperature) if temperature is not None else 0.2,
            "max_tokens": 2048,
        }

        if response_mime_type and response_mime_type.lower() == "application/json":
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Groq request failed ({exc.code}): {detail}") from exc
        except Exception as exc:  # pragma: no cover - network transport errors
            raise ProviderError(f"Groq request failed: {exc}") from exc

        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError("Groq returned invalid JSON.") from exc

        choices = result.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError("Groq returned no choices.")

        first = choices[0]
        message = first.get("message", {}) if isinstance(first, dict) else {}
        content = message.get("content") if isinstance(message, dict) else None

        if isinstance(content, list):
            text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )
        elif isinstance(content, str):
            text = content
        else:
            text = ""

        if not isinstance(text, str) or not text.strip():
            raise ProviderError("Groq returned an empty response.")

        return text.strip()


class GrokClient(GroqClient):
    """Backward-compatible alias for the older Grok naming used across the project."""

    def __init__(self, api_key: str | None = None, model: str | None = None, *, timeout_seconds: float = 60.0) -> None:
        super().__init__(
            api_key=api_key or get_grok_api_key(),
            model=model or settings.groq_model,
            timeout_seconds=timeout_seconds,
            base_url="https://api.x.ai/v1/chat/completions",
        )


class ProviderRouter:
    """Use Gemini first and fallback to Grok if Gemini is unavailable or rate-limited."""

    def __init__(
        self,
        *,
        preferred_provider: str = "auto",
        providers: Iterable[str] | None = None,
    ) -> None:
        self.preferred_provider = preferred_provider.lower()
        order = list(providers) if providers is not None else ["gemini", "groq", "grok"]
        order = [provider.lower() for provider in order]

        if self.preferred_provider == "gemini":
            order = ["gemini", *[p for p in order if p != "gemini"]]
        elif self.preferred_provider in {"grok", "groq"}:
            order = [self.preferred_provider, *[p for p in order if p != self.preferred_provider]]

        self.providers: list[tuple[str, Any]] = []
        for provider_name in order:
            if provider_name == "gemini":
                if get_api_key():
                    self.providers.append(("gemini", GeminiClient()))
            elif provider_name in {"groq", "grok"}:
                if get_grok_api_key():
                    self.providers.append((provider_name, GroqClient()))

        if not self.providers:
            raise ProviderFallbackError(
                "No configured AI providers are available. Set GEMINI_API_KEY or GROQ_API_KEY/GROK_API_KEY/XAI_API_KEY."
            )

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float | None = 0.2,
        response_mime_type: str | None = None,
        system: str | None = None,
    ) -> str:
        last_error: Exception | None = None
        for provider_name, client in self.providers:
            try:
                return client.generate_text(
                    prompt,
                    temperature=temperature,
                    response_mime_type=response_mime_type,
                    system=system,
                )
            except Exception as exc:  # pragma: no cover - the router is intentionally fallback-oriented
                last_error = exc
                continue

        raise ProviderFallbackError(
            f"All configured providers failed: {', '.join(name for name, _ in self.providers)}"
        ) from last_error

    def generate(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> str:
        return self.generate_text(prompt, system=system, **kwargs)


def get_default_provider_router() -> ProviderRouter:
    """Create the default provider router using the configured preference order."""
    return ProviderRouter(preferred_provider=settings.preferred_provider)


__all__ = [
    "GrokClient",
    "ProviderError",
    "ProviderFallbackError",
    "ProviderRouter",
    "get_default_provider_router",
]
