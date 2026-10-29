"""Hybrid BM25 and FAISS retrieval over course material."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from lighted_ai.config import settings
from lighted_ai.embeddings import embed_batch, embed_text
from lighted_ai.ingestion.pipeline import IngestedDocument

_RRF_K = 60
_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
EmbeddingSignature = tuple[str, str, int]


@dataclass
class Document:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    document: Document
    score: float


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.casefold())


def _embedding_signature() -> EmbeddingSignature:
    if settings.embedding_provider == "gemini":
        return (
            settings.embedding_provider,
            settings.embedding_model,
            settings.gemini_embedding_dimensions,
        )
    return (
        settings.embedding_provider,
        settings.sentence_model,
        0,
    )


class Retriever:
    """Hybrid lexical and dense retriever with reciprocal-rank fusion."""

    def __init__(self) -> None:
        self._docs: list[Document] = []
        self._index: faiss.IndexFlatIP | None = None
        self._bm25: BM25Okapi | None = None
        self._embedding_signature: EmbeddingSignature | None = None

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return

        signature = _embedding_signature()
        if (
            self._embedding_signature is not None
            and signature != self._embedding_signature
        ):
            raise RuntimeError(
                "Embedding configuration changed after indexing. "
                "Create a new retriever and rebuild the index."
            )

        vectors = embed_batch([document.text for document in docs])
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(docs) or matrix.shape[1] == 0:
            raise ValueError("Document embeddings must form a non-empty 2D matrix")
        if not np.isfinite(matrix).all():
            raise ValueError("Document embeddings must contain only finite values")

        norms = np.linalg.norm(matrix, axis=1)
        if np.any(norms == 0):
            raise ValueError("Document embeddings must not be zero vectors")
        matrix = matrix / norms[:, np.newaxis]

        if self._index is not None and matrix.shape[1] != self._index.d:
            raise ValueError(
                "Embedding dimensions do not match the existing FAISS index: "
                f"{matrix.shape[1]} != {self._index.d}"
            )

        updated_docs = [*self._docs, *docs]
        updated_bm25 = BM25Okapi(
            [_tokenize(document.text) for document in updated_docs]
        )

        index = (
            faiss.IndexFlatIP(matrix.shape[1])
            if self._index is None
            else faiss.clone_index(self._index)
        )
        index.add(matrix)
        self._index = index
        self._docs = updated_docs
        self._bm25 = updated_bm25
        self._embedding_signature = signature

    def index_lessons(self, lessons: list[dict[str, Any]]) -> None:
        """Index lessons shaped as {id, title, content}."""
        docs = [
            Document(
                id=str(lesson.get("id")),
                text=f"{lesson.get('title', '')}\n{lesson.get('content', '')}",
                metadata={"title": lesson.get("title", "")},
            )
            for lesson in lessons
        ]
        self.add_documents(docs)

    def add_ingested_documents(
        self,
        documents: list[IngestedDocument] | tuple[IngestedDocument, ...],
    ) -> None:
        """Index parent/child chunks produced by the ingestion pipeline."""
        chunk_documents: list[Document] = []
        for ingested in documents:
            if not isinstance(ingested, IngestedDocument):
                raise TypeError("Each item must be an IngestedDocument")
            for chunk in ingested.chunks:
                metadata = {
                    "source_name": ingested.source_name,
                    "source_type": ingested.source_type,
                    "chunk_level": chunk.chunk_level,
                    "parent_chunk_id": chunk.parent_chunk_id,
                    "location": chunk.location,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                    "source_metadata": dict(ingested.metadata),
                }
                chunk_documents.append(
                    Document(
                        id=chunk.chunk_id,
                        text=chunk.content,
                        metadata=metadata,
                    )
                )
        if chunk_documents:
            self.add_documents(chunk_documents)

    def add_ingested_file(
        self,
        file_bytes: bytes | bytearray | memoryview,
        filename: str,
    ) -> None:
        """Helper to ingest a single file and immediately index its chunks."""
        from lighted_ai.ingestion.pipeline import ingest_file

        self.add_ingested_documents([ingest_file(file_bytes, filename)])

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        if not self._docs:
            return []
        if _embedding_signature() != self._embedding_signature:
            raise RuntimeError(
                "Embedding configuration changed after indexing. "
                "Create a new retriever and rebuild the index."
            )

        query_vector = np.asarray(
            embed_text(query, task_type="RETRIEVAL_QUERY"),
            dtype=np.float32,
        )
        if query_vector.ndim != 1 or query_vector.size != self._index.d:
            raise ValueError(
                f"Query embedding must have {self._index.d} dimensions"
            )
        if not np.isfinite(query_vector).all():
            raise ValueError("Query embedding must contain only finite values")
        query_norm = float(np.linalg.norm(query_vector))
        if query_norm == 0:
            raise ValueError("Query embedding must not be a zero vector")
        query_vector /= query_norm

        _, dense_ids = self._index.search(
            query_vector.reshape(1, -1),
            len(self._docs),
        )
        dense_ranking = [int(document_id) for document_id in dense_ids[0]]

        lexical_scores = self._bm25.get_scores(_tokenize(query))
        lexical_ranking = [
            int(document_id)
            for document_id in np.argsort(-lexical_scores, kind="stable")
            if lexical_scores[document_id] > 0
        ]

        fused_scores = [0.0] * len(self._docs)
        for ranking in (dense_ranking, lexical_ranking):
            for rank, document_id in enumerate(ranking, start=1):
                fused_scores[document_id] += 1.0 / (_RRF_K + rank)

        ranked_ids = sorted(
            range(len(self._docs)),
            key=lambda document_id: fused_scores[document_id],
            reverse=True,
        )
        return [
            SearchResult(
                document=self._docs[document_id],
                score=fused_scores[document_id],
            )
            for document_id in ranked_ids[:top_k]
        ]


def build_retriever_from_ingested_documents(
    documents: list[IngestedDocument] | tuple[IngestedDocument, ...],
) -> Retriever:
    """Convenience constructor for indexing ingested material in one step."""
    retriever = Retriever()
    retriever.add_ingested_documents(documents)
    return retriever


# A shared default retriever the backend can populate at startup.
default_retriever = Retriever()
