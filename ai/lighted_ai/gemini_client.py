"""Thin wrapper around the Google Gemini API.

Keeps all provider-specific code in one place so the rest of the AI module
(and the backend) never imports `google.generativeai` directly.
"""
from __future__ import annotations

import logging

from lighted_ai.config import get_api_key, settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or get_api_key()
        self.model_name = model or settings.gemini_model
        self._model = None

    def _ensure(self):
        if self._model is not None:
            return
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env to enable AI features."
            )
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Generate text from a prompt. Returns a plain string."""
        self._ensure()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            resp = self._model.generate_content(full_prompt)
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gemini generation failed")
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc

    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the given text."""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        result = genai.embed_content(
            model=f"models/{settings.embedding_model}",
            content=text,
            task_type="retrieval_document",
        )
        return list(result["embedding"])


# Module-level default client (lazy — no network call until used)
default_client = GeminiClient()
