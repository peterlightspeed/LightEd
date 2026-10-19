"""Embeddings helpers.

Uses Gemini embeddings when an API key is present, and falls back to a
deterministic local hashing embedding so the pipeline works offline / in tests.
"""
from __future__ import annotations

import hashlib

import numpy as np

from lighted_ai.config import get_api_key
from lighted_ai.gemini_client import GeminiClient

_DIM = 256


def _hash_embedding(text: str, dim: int = _DIM) -> list[float]:
    """Deterministic bag-of-words hashing embedding (no network needed)."""
    vec = np.zeros(dim, dtype=np.float32)
    for token in text.lower().split():
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = np.linalg.norm(vec)
    return (vec / norm).tolist() if norm > 0 else vec.tolist()


def embed_text(text: str, client: GeminiClient | None = None) -> list[float]:
    """Embed a single piece of text."""
    if get_api_key():
        try:
            return (client or GeminiClient()).embed(text)
        except Exception:  # noqa: BLE001 — graceful fallback
            pass
    return _hash_embedding(text)


def embed_batch(texts: list[str], client: GeminiClient | None = None) -> list[list[float]]:
    return [embed_text(t, client=client) for t in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1e-9
    return float(np.dot(va, vb) / denom)
