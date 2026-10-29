
"""Production-oriented embedding helpers.

Primary provider:
    Gemini gemini-embedding-001, 3072 dimensions.

Local provider:
    Sentence Transformers, all-MiniLM-L6-v2, 384 dimensions by default.

IMPORTANT:
    These providers generate incompatible embedding spaces. Select one
    provider per vector index. Never switch providers for an existing index
    without rebuilding that index or routing to a separate index.

Environment:
    LIGHTED_EMBEDDING_PROVIDER=gemini
    LIGHTED_GEMINI_MODEL=gemini-embedding-001
    LIGHTED_GEMINI_DIMENSIONS=3072
    LIGHTED_SENTENCE_MODEL=sentence-transformers/all-MiniLM-L6-v2
"""

from __future__ import annotations

import logging
import math
import os
import threading
import unicodedata
from collections.abc import Sequence
from functools import lru_cache
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from lighted_ai.config import get_api_key
from lighted_ai.gemini_client import GeminiClient

log = logging.getLogger(__name__)

EmbeddingTask = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]
Vector = list[float]
FloatArray = NDArray[np.float32]

GEMINI_MODEL = os.getenv(
    "LIGHTED_GEMINI_MODEL", "gemini-embedding-001"
)
GEMINI_DIMENSIONS = int(
    os.getenv("LIGHTED_GEMINI_DIMENSIONS", "3072")
)

SENTENCE_MODEL = os.getenv(
    "LIGHTED_SENTENCE_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

PROVIDER = os.getenv(
    "LIGHTED_EMBEDDING_PROVIDER", "gemini"
).strip().lower()

GEMINI_TASKS = {"RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"}

# Protect lazy initialization if requests arrive concurrently.
_MODEL_LOCK = threading.Lock()


def _validate_text(text: str) -> str:
    """Validate and consistently normalize input text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = unicodedata.normalize("NFC", text)

    if not text.strip():
        raise ValueError("text must not be empty or whitespace-only")

    return text


def _validate_task(task_type: str) -> EmbeddingTask:
    """Accept only retrieval tasks supported by this module."""
    if task_type not in GEMINI_TASKS:
        raise ValueError(
            f"Unsupported task_type {task_type!r}; "
            f"expected one of {sorted(GEMINI_TASKS)}"
        )

    return task_type  # type: ignore[return-value]


def _validate_dimensions(dimensions: int) -> int:
    """Validate the configured Gemini output dimension."""
    if (
        isinstance(dimensions, bool)
        or not isinstance(dimensions, int)
        or not 1 <= dimensions <= 3072
    ):
        raise ValueError(
            "Gemini dimensions must be an integer between 1 and 3072"
        )

    return dimensions


def _normalize(vector: Any) -> Vector:
    """Validate a vector and return a unit-normalized Python list."""
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


def _validate_embedding(vector: Any,*,expected_dimensions: int,) -> Vector:
    """Validate vector shape, values, and configured dimensionality."""
    result = _normalize(vector)

    if len(result) != expected_dimensions:
        raise ValueError(
            "Embedding dimension mismatch: "
            f"expected {expected_dimensions}, got {len(result)}"
        )

    return result


@lru_cache(maxsize=1)
def _load_sentence_transformer(model_name: str) -> Any:
    """Load the local model once and cache it for subsequent requests."""
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


def _sentence_embedding(text: str) -> Vector:
    """Generate a normalized embedding using the local model."""
    model = _load_sentence_transformer(SENTENCE_MODEL)

    result = model.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    if result.ndim != 2 or result.shape[0] != 1:
        raise ValueError(
            f"Unexpected Sentence Transformers output shape: {result.shape}"
        )

    vector = _normalize(result[0])

    # The model's real output dimension is authoritative.
    expected_dimensions = int(model.get_sentence_embedding_dimension())

    if len(vector) != expected_dimensions:
        raise ValueError(
            "Local model dimension mismatch: "
            f"expected {expected_dimensions}, got {len(vector)}"
        )

    return vector


def _get_gemini_client(
    client: GeminiClient | None,
) -> GeminiClient:
    """Return an initialized Gemini client or raise a clear error."""
    if client is not None:
        return client

    if not get_api_key():
        raise RuntimeError(
            "Gemini provider selected but no API key is configured. "
            "Set the API key or explicitly select the local provider."
        )

    return GeminiClient()


def _gemini_embedding(
    text: str,
    *,
    task_type: EmbeddingTask,
    client: GeminiClient,
) -> Vector:
    """Generate a Gemini embedding for a specified retrieval task.

    GeminiClient.embed must accept task_type and output_dimensionality.
    See the client interface notes below.
    """
    result = client.embed(
        text,
        task_type=task_type,
        output_dimensionality=GEMINI_DIMENSIONS,
    )

    return _validate_embedding(
        result,
        expected_dimensions=GEMINI_DIMENSIONS,
    )


def embed_text(
    text: str,
    client: GeminiClient | None = None,
    *,
    task_type: EmbeddingTask = "RETRIEVAL_DOCUMENT",
) -> Vector:
    """Embed one text using the explicitly configured provider.

    Use RETRIEVAL_DOCUMENT when indexing content.
    Use RETRIEVAL_QUERY when embedding a search query.

    Provider errors are deliberately propagated. Silent failover could
    contaminate a vector index with embeddings from another model.
    """
    text = _validate_text(text)
    task_type = _validate_task(task_type)

    if PROVIDER == "gemini":
        remote = _get_gemini_client(client)
        return _gemini_embedding(
            text,
            task_type=task_type,
            client=remote,
        )

    if PROVIDER == "sentence-transformers":
        return _sentence_embedding(text)

    raise ValueError(
        f"Unsupported embedding provider {PROVIDER!r}. "
        "Choose 'gemini' or 'sentence-transformers'."
    )


def embed_batch(
    texts: Sequence[str],
    client: GeminiClient | None = None,
    *,
    task_type: EmbeddingTask = "RETRIEVAL_DOCUMENT",
) -> list[Vector]:
    """Embed multiple texts using one explicitly selected provider.

    This method validates the complete batch before embedding. It uses
    sequential requests unless GeminiClient provides its own batch method.
    All returned vectors must have the same dimension.
    """
    if isinstance(texts, (str, bytes)):
        raise TypeError("texts must be a sequence of strings")

    normalized_texts = [_validate_text(text) for text in texts]
    task_type = _validate_task(task_type)

    if not normalized_texts:
        return []

    if PROVIDER == "sentence-transformers":
        model = _load_sentence_transformer(SENTENCE_MODEL)

        result = model.encode(
            normalized_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        if result.ndim != 2 or result.shape[0] != len(normalized_texts):
            raise ValueError(
                "Unexpected Sentence Transformers batch output shape"
            )

        dimensions = int(model.get_sentence_embedding_dimension())

        vectors = [
            _validate_embedding(
                vector,
                expected_dimensions=dimensions,
            )
            for vector in result
        ]

    elif PROVIDER == "gemini":
        remote = _get_gemini_client(client)

        batch_method = getattr(remote, "embed_batch", None)

        if callable(batch_method):
            raw_vectors = batch_method(
                normalized_texts,
                task_type=task_type,
                output_dimensionality=GEMINI_DIMENSIONS,
            )

            if len(raw_vectors) != len(normalized_texts):
                raise ValueError(
                    "Gemini returned an unexpected number of embeddings"
                )

            vectors = [
                _validate_embedding(
                    vector,
                    expected_dimensions=GEMINI_DIMENSIONS,
                )
                for vector in raw_vectors
            ]
        else:
            vectors = [
                _gemini_embedding(
                    text,
                    task_type=task_type,
                    client=remote,
                )
                for text in normalized_texts
            ]

    else:
        raise ValueError(
            f"Unsupported embedding provider {PROVIDER!r}. "
            "Choose 'gemini' or 'sentence-transformers'."
        )

    dimensions = {len(vector) for vector in vectors}

    if len(dimensions) != 1:
        raise ValueError("Batch contains inconsistent embedding dimensions")

    return vectors


def cosine_similarity(
    a: Sequence[float],
    b: Sequence[float],
) -> float:
    """Compute cosine similarity for compatible embedding vectors.

    Returns a value between -1 and 1. Rejects invalid vectors and dimension
    mismatches rather than silently returning misleading similarity scores.
    """
    try:
        va = np.asarray(a, dtype=np.float64)
        vb = np.asarray(b, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("Vectors must contain numeric values") from exc

    if va.ndim != 1 or vb.ndim != 1:
        raise ValueError("Vectors must be one-dimensional")

    if va.size == 0 or vb.size == 0:
        raise ValueError("Vectors must not be empty")

    if va.shape != vb.shape:
        raise ValueError(
            f"Embedding dimensions do not match: {va.size} != {vb.size}"
        )

    if not np.isfinite(va).all() or not np.isfinite(vb).all():
        raise ValueError("Vectors must contain only finite values")

    norm_a = float(np.linalg.norm(va))
    norm_b = float(np.linalg.norm(vb))

    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("Cannot compute cosine similarity for zero vectors")

    similarity = float(np.dot(va, vb) / (norm_a * norm_b))

    return max(-1.0, min(1.0, similarity))
