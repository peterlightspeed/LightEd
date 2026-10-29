"""Compatibility exports for embedding helpers."""

from lighted_ai.embeddings import (
    EmbeddingTask,
    FloatArray,
    Vector,
    cosine_similarity,
    embed_batch,
    embed_text,
)

__all__ = [
    "EmbeddingTask",
    "FloatArray",
    "Vector",
    "cosine_similarity",
    "embed_batch",
    "embed_text",
]
