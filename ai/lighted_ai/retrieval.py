"""Retrieval over course material (RAG).

Sprint 1 uses an in-memory store with cosine similarity so the whole team can
run it without extra infra. FAISS can be swapped in later behind the same API.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lighted_ai.embeddings import cosine_similarity, embed_batch, embed_text


@dataclass
class Document:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    document: Document
    score: float


class Retriever:
    """Simple vector retriever over a set of documents."""

    def __init__(self) -> None:
        self._docs: list[Document] = []
        self._vectors: list[list[float]] = []

    def add_documents(self, docs: list[Document]) -> None:
        texts = [d.text for d in docs]
        vectors = embed_batch(texts)
        self._docs.extend(docs)
        self._vectors.extend(vectors)

    def index_lessons(self, lessons: list[dict]) -> None:
        """Convenience: index lessons shaped as {id, title, content}."""
        docs = [
            Document(
                id=str(lesson.get("id")),
                text=f"{lesson.get('title', '')}\n{lesson.get('content', '')}",
                metadata={"title": lesson.get("title", "")},
            )
            for lesson in lessons
        ]
        self.add_documents(docs)

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        if not self._docs:
            return []
        q_vec = embed_text(query)
        scored = [
            SearchResult(document=doc, score=cosine_similarity(q_vec, vec))
            for doc, vec in zip(self._docs, self._vectors, strict=False)
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


# A shared default retriever the backend can populate at startup.
default_retriever = Retriever()
