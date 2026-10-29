"""AI tutor: retrieve relevant course context, then answer via the provider router."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lighted_ai.gemini_client import GeminiClient
from lighted_ai.provider_router import ProviderRouter, ProviderFallbackError
from lighted_ai.retrieval import default_retriever

SYSTEM_PROMPT = (
    "You are LightEd, a friendly and concise AI tutor for students. "
    "Answer using only the provided course context when possible. "
    "If the context is insufficient, say so plainly and give a helpful general explanation. "
    "Keep answers clear, structured, encouraging, and brief. "
    "When relevant, mention the closest source topic in plain language, and do not invent facts."
)

MAX_CONTEXT_CHARS = 6000


@dataclass
class TutorAnswer:
    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)

    @property
    def source_titles(self) -> list[str]:
        return [source.get("title", "Untitled") for source in self.sources]

    @property
    def frontend_sources(self) -> list[dict[str, Any]]:
        return [dict(source) for source in self.sources]


def _normalise_question(question: str) -> str:
    if not isinstance(question, str):
        raise TypeError("question must be a string")
    cleaned = question.strip()
    if not cleaned:
        raise ValueError("question must not be empty")
    return cleaned


def _as_frontend_source(document: Any, *, score: float | None = None) -> dict[str, Any]:
    metadata = getattr(document, "metadata", {}) or {}
    title = str(metadata.get("title") or getattr(document, "id", "Untitled") or "Untitled")
    snippet = str(getattr(document, "text", "")).strip()
    return {
        "title": title,
        "id": str(getattr(document, "id", title)),
        "snippet": snippet[:220] + ("..." if len(snippet) > 220 else ""),
        "source_type": metadata.get("source_type"),
        "location": metadata.get("location"),
        "score": float(score) if score is not None else None,
    }


def _build_context(results: list, *, max_chars: int = MAX_CONTEXT_CHARS) -> tuple[str, list[dict[str, Any]]]:
    chunks: list[str] = []
    sources: list[dict[str, Any]] = []
    used_chars = 0

    for result in results:
        document = result.document
        source = _as_frontend_source(document, score=getattr(result, "score", None))
        if source not in sources:
            sources.append(source)

        text = str(document.text).strip()
        if not text:
            continue

        title = source["title"]
        chunk = f"[{title}] {text}"
        if used_chars + len(chunk) > max_chars:
            remaining = max_chars - used_chars
            if remaining > 200:
                chunks.append(chunk[:remaining].rstrip() + "...")
            break
        chunks.append(chunk)
        used_chars += len(chunk)

    return "\n\n".join(chunks), sources


def answer_question(
    question: str,
    course_id: int | None = None,
    retriever=None,
    client: GeminiClient | None = None,
) -> TutorAnswer:
    """Answer a question using the best retrieved course context.

    The function prefers grounded answers from retrieved material, but falls back to a
    helpful general answer when the course context is missing or the model is unavailable.
    """
    cleaned_question = _normalise_question(question)
    retriever = retriever or default_retriever
    results = retriever.search(cleaned_question, top_k=3)

    context, sources = _build_context(results)

    if not context:
        fallback = (
            "I couldn't find enough course material to answer that confidently. "
            "Please provide a specific question or add more lesson content."
        )
        return TutorAnswer(answer=fallback, sources=[])

    prompt = (
        "Course context:\n"
        f"{context}\n\n"
        f"Student question: {cleaned_question}"
    )

    try:
        active_client = client or _default_answer_client()
        answer = active_client.generate(prompt, system=SYSTEM_PROMPT)
    except Exception:  # noqa: BLE001 — offline / no key fallback
        answer = (
            "I couldn't reach the AI model right now, but here is the most relevant "
            "course material I found:\n\n"
            f"{context}"
        )

    return TutorAnswer(answer=answer.strip(), sources=sources)


def _default_answer_client():
    """Return the best available routed provider client for tutoring."""
    try:
        return ProviderRouter()
    except ProviderFallbackError:
        return GeminiClient()
