
"""Centralized Gemini client for LightEd.

This implementation targets the legacy google.generativeai SDK used by the
current project. Pin and test that dependency version. For a new deployment,
consider migrating the wrapper and embedding calls together to google-genai.
"""
from __future__ import annotations

import logging
import random
import time
from typing import Literal, Any

from google.api_core import exceptions as google_exceptions

from lighted_ai.config import get_api_key, settings

logger = logging.getLogger(__name__)

RETRYABLE_ERRORS = (
    google_exceptions.DeadlineExceeded,
    google_exceptions.ServiceUnavailable,
    google_exceptions.ResourceExhausted,
    google_exceptions.InternalServerError,
)


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        timeout_seconds: float = 120.0,
        max_retries: int = 4,
    ) -> None:
        key = api_key if api_key is not None else get_api_key()
        if not isinstance(key, str) or not key.strip():
            key = None

        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive.")

        if (
            isinstance(max_retries, bool)
            or not isinstance(max_retries, int)
            or max_retries < 1
        ):
            raise ValueError("max_retries must be an integer >= 1.")

        selected_model = model if model is not None else settings.gemini_model
        if not isinstance(selected_model, str) or not selected_model.strip():
            raise ValueError("model must be a non-empty string.")

        self.api_key = key
        self.model_name = selected_model.strip()
        self.timeout_seconds = float(timeout_seconds)
        self.max_retries = max_retries
        self._model: Any | None = None

    def _ensure(self) -> None:
        if self._model is not None:
            return

        if not self.api_key:
            raise RuntimeError(
                "Gemini API key is not configured. Set GEMINI_API_KEY "
                "or LIGHTED_GEMINI_API_KEY."
            )

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "The google-generativeai package is required for Gemini."
            ) from exc

        # Note: this SDK configures credentials globally. Do not use this
        # legacy wrapper for concurrent per-tenant API keys in one process.
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model_name)

    def _call_with_retry(self, fn, *args, **kwargs):
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except RETRYABLE_ERRORS as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break

                base_delay = min(2 ** (attempt - 1), 8)
                delay = base_delay + random.uniform(0.0, 0.25 * base_delay)
                logger.warning(
                    "Transient Gemini error (%s); retry %d/%d in %.2fs.",
                    type(exc).__name__,
                    attempt,
                    self.max_retries,
                    delay,
                )
                time.sleep(delay)

        raise RuntimeError(
            f"Gemini request failed after {self.max_retries} attempts."
        ) from last_error

    def generate(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        """Generate plain text."""
        return self.generate_text(prompt, system=system)

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float | None = 0.2,
        response_mime_type: str | None = None,
        system: str | None = None,
    ) -> str:
        """Generate text with optional temperature and MIME type."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string.")

        if system is not None and not isinstance(system, str):
            raise TypeError("system must be a string or None.")

        if temperature is not None:
            if (
                isinstance(temperature, bool)
                or not isinstance(temperature, (int, float))
                or not 0.0 <= temperature <= 2.0
            ):
                raise ValueError("temperature must be between 0 and 2.")

        if response_mime_type is not None and not isinstance(
            response_mime_type, str
        ):
            raise TypeError("response_mime_type must be a string or None.")

        self._ensure()
        full_prompt = f"{system.strip()}\n\n{prompt}" if system and system.strip() else prompt

        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = float(temperature)
        if response_mime_type is not None:
            generation_config["response_mime_type"] = response_mime_type

        kwargs: dict[str, Any] = {
            "request_options": {"timeout": self.timeout_seconds},
        }
        if generation_config:
            kwargs["generation_config"] = generation_config

        response = self._call_with_retry(
            self._model.generate_content,
            full_prompt,
            **kwargs,
        )

        # Some blocked or safety-filtered responses have no text.
        try:
            text = response.text
        except (AttributeError, ValueError) as exc:
            raise RuntimeError(
                "Gemini returned no readable text. The response may have "
                "been blocked or may contain no text candidate."
            ) from exc

        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Gemini returned an empty text response.")

        return text.strip()

    def embed(
        self,
        text: str,
        *,
        task_type: Literal[
            "RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"
        ] = "RETRIEVAL_DOCUMENT",
        output_dimensionality: int | None = None,
    ) -> list[float]:
        """Return a single retrieval embedding."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string.")

        if task_type not in ("RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"):
            raise ValueError("Unsupported embedding task_type.")

        dimensions = (
            settings.gemini_embedding_dimensions
            if output_dimensionality is None
            else output_dimensionality
        )
        if (
            isinstance(dimensions, bool)
            or not isinstance(dimensions, int)
            or not 1 <= dimensions <= 3072
        ):
            raise ValueError("output_dimensionality must be between 1 and 3072.")

        if not self.api_key:
            raise RuntimeError("Gemini API key is not configured.")

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "The google-generativeai package is required for embeddings."
            ) from exc

        genai.configure(api_key=self.api_key)

        result = self._call_with_retry(
            genai.embed_content,
            model=f"models/{settings.embedding_model}",
            content=text,
            task_type=task_type.lower(),
            output_dimensionality=dimensions,
            request_options={"timeout": self.timeout_seconds},
        )

        embedding = result.get("embedding") if isinstance(result, dict) else None
        if not isinstance(embedding, (list, tuple)) or not embedding:
            raise RuntimeError("Gemini returned an invalid embedding response.")

        return list(embedding)


default_client = GeminiClient()
