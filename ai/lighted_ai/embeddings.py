"""Validated embedding helpers for Gemini and Sentence Transformers."""
from __future__ import annotations

import logging
import math
import threading
import unicodedata
from collections.abc import Sequence
from functools import lru_cache
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from lighted_ai.config import get_api_key, settings
from lighted_ai.gemini_client import GeminiClient

log = logging.getLogger(__name__)

EmbeddingTask = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]
Vector = list[float]
FloatArray = NDArray[np.float32]
_GEMINI_TASKS = frozenset(("RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"))
_MODEL_LOCK = threading.Lock()


def _validate_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalized = unicodedata.normalize("NFC", text)
    if not normalized.strip():
        raise ValueError("text must not be empty or whitespace-only")
    return normalized


def _validate_task(task_type: str) -> EmbeddingTask:
    if task_type == "RETRIEVAL_DOCUMENT":
        return "RETRIEVAL_DOCUMENT"
    if task_type == "RETRIEVAL_QUERY":
        return "RETRIEVAL_QUERY"
    raise ValueError(
        f"Unsupported task_type {task_type!r}; "
        "expected 'RETRIEVAL_DOCUMENT' or 'RETRIEVAL_QUERY'"
    )


def _validate_dimensions(dimensions: int) -> int:
    if (
        isinstance(dimensions, bool)
        or not isinstance(dimensions, int)
        or not 1 <= dimensions <= 3072
    ):
        raise ValueError("Gemini dimensions must be an integer between 1 and 3072")
    return dimensions


def _normalize(vector: Any) -> Vector:
    try:
        values = np.asarray(vector, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise ValueError("Embedding must contain numeric values") from exc

    if values.ndim != 1 or values.size == 0:
        raise ValueError("Embedding must be a non-empty 1D vector")
    if not np.isfinite(values).all():
        raise ValueError("Embedding contains NaN or infinite values")

    norm = float(np.linalg.norm(values))
    if not math.isfinite(norm) or norm == 0.0:
        raise ValueError("Embedding must have a finite, non-zero norm")
    return (values / norm).tolist()


def _validate_embedding(vector: Any, expected_dimensions: int) -> Vector:
    result = _normalize(vector)
    if len(result) != expected_dimensions:
        raise ValueError(
            f"Embedding dimension mismatch: expected {expected_dimensions}, "
            f"got {len(result)}"
        )
    return result


@lru_cache(maxsize=1)
def _load_sentence_transformer(model_name: str) -> Any:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Sentence Transformers is not installed. "
            "Install it with: pip install sentence-transformers"
        ) from exc

    with _MODEL_LOCK:
        log.info("Loading Sentence Transformers model: %s", model_name)
        return SentenceTransformer(model_name)


def _sentence_embeddings(texts: Sequence[str]) -> list[Vector]:
    model = _load_sentence_transformer(settings.sentence_model)
    result = model.encode(
        list(texts),
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    if result.ndim != 2 or result.shape[0] != len(texts):
        raise ValueError("Unexpected Sentence Transformers batch output shape")

    dimensions = int(model.get_sentence_embedding_dimension())
    return [
        _validate_embedding(vector, expected_dimensions=dimensions)
        for vector in result
    ]


def _get_gemini_client(client: GeminiClient | None) -> GeminiClient:
    if client is not None:
        return client
    if not get_api_key():
        raise RuntimeError(
            "Gemini provider selected but no API key is configured. "
            "Set GEMINI_API_KEY or select the Sentence Transformers provider."
        )
    return GeminiClient()


def _gemini_embedding(
    text: str,
    *,
    task_type: EmbeddingTask,
    client: GeminiClient,
) -> Vector:
    dimensions = _validate_dimensions(settings.gemini_embedding_dimensions)
    result = client.embed(
        text,
        task_type=task_type,
        output_dimensionality=dimensions,
    )
    return _validate_embedding(result, expected_dimensions=dimensions)


def embed_text(
    text: str,
    client: GeminiClient | None = None,
    *,
    task_type: EmbeddingTask = "RETRIEVAL_DOCUMENT",
) -> Vector:
    """Embed one text using the configured provider; provider errors propagate."""
    normalized_text = _validate_text(text)
    task_type = _validate_task(task_type)

    if settings.embedding_provider == "gemini":
        return _gemini_embedding(
            normalized_text,
            task_type=task_type,
            client=_get_gemini_client(client),
        )
    if settings.embedding_provider == "sentence-transformers":
        return _sentence_embeddings([normalized_text])[0]
    raise ValueError(f"Unsupported embedding provider {settings.embedding_provider!r}")


def embed_batch(
    texts: Sequence[str],
    client: GeminiClient | None = None,
    *,
    task_type: EmbeddingTask = "RETRIEVAL_DOCUMENT",
) -> list[Vector]:
    """Embed a sequence and ensure all input and output dimensions are consistent."""
    if isinstance(texts, (str, bytes)):
        raise TypeError("texts must be a sequence of strings")

    normalized_texts = [_validate_text(text) for text in texts]
    task_type = _validate_task(task_type)
    if not normalized_texts:
        return []

    if settings.embedding_provider == "sentence-transformers":
        vectors = _sentence_embeddings(normalized_texts)
    elif settings.embedding_provider == "gemini":
        remote = _get_gemini_client(client)
        vectors = [
            _gemini_embedding(text, task_type=task_type, client=remote)
            for text in normalized_texts
        ]
    else:
        raise ValueError(f"Unsupported embedding provider {settings.embedding_provider!r}")

    if len({len(vector) for vector in vectors}) != 1:
        raise ValueError("Batch contains inconsistent embedding dimensions")
    return vectors


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity, rejecting invalid or incompatible vectors."""
    try:
        vector_a = np.asarray(a, dtype=np.float64)
        vector_b = np.asarray(b, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("Vectors must contain numeric values") from exc

    if vector_a.ndim != 1 or vector_b.ndim != 1:
        raise ValueError("Vectors must be one-dimensional")
    if vector_a.size == 0 or vector_b.size == 0:
        raise ValueError("Vectors must not be empty")
    if vector_a.shape != vector_b.shape:
        raise ValueError(
            f"Embedding dimensions do not match: {vector_a.size} != {vector_b.size}"
        )
    if not np.isfinite(vector_a).all() or not np.isfinite(vector_b).all():
        raise ValueError("Vectors must contain only finite values")

    norm_a = float(np.linalg.norm(vector_a))
    norm_b = float(np.linalg.norm(vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("Cannot compute cosine similarity for zero vectors")

    similarity = float(np.dot(vector_a, vector_b) / (norm_a * norm_b))
    return max(-1.0, min(1.0, similarity))