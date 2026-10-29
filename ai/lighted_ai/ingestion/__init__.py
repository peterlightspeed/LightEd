"""Light ingestion utilities for the AI module.

This keeps the multimodal ingestion pipeline small and practical for the
current LightEd AI subsystem: PDF, TXT, PPTX, and audio inputs are supported,
while graph-db and orchestration-heavy pieces are intentionally excluded.
"""

from lighted_ai.ingestion.pipeline import (
    Chunk,
    IngestedDocument,
    ingest_file,
    ingest_files,
    semantic_parent_child_chunks,
)

__all__ = [
    "Chunk",
    "IngestedDocument",
    "ingest_file",
    "ingest_files",
    "semantic_parent_child_chunks",
]
