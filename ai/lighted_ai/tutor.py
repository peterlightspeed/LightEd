"""AI tutor: retrieve relevant course context, then answer with Gemini."""
from __future__ import annotations

from dataclasses import dataclass

from lighted_ai.gemini_client import GeminiClient
from lighted_ai.retrieval import default_retriever

SYSTEM_PROMPT = (
    "You are LightEd, a friendly and concise AI tutor for students. "
    "Answer using ONLY the provided course context when possible. "
    "If the context is insufficient, say so and give a helpful general explanation. "
    "Keep answers clear, structured, and encouraging."
)


@dataclass
class TutorAnswer:
    answer: str
    sources: list[str]


def answer_question(
    question: str,
    course_id: int | None = None,
    retriever=None,
    client: GeminiClient | None = None,
) -> TutorAnswer:
    retriever = retriever or default_retriever
    results = retriever.search(question, top_k=3)

    context = "\n\n".join(
        f"[{r.document.metadata.get('title', r.document.id)}] {r.document.text}"
        for r in results
    )
    sources = [r.document.metadata.get("title", r.document.id) for r in results]

    prompt = (
        f"Course context:\n{context or '(no context available)'}\n\n"
        f"Student question: {question}"
    )

    try:
        answer = (client or GeminiClient()).generate(prompt, system=SYSTEM_PROMPT)
    except Exception:  # noqa: BLE001 — offline / no key fallback
        answer = (
            "I couldn't reach the AI model right now, but here is the most relevant "
            f"material I found:\n\n{context or 'No course material indexed yet.'}"
        )
    return TutorAnswer(answer=answer, sources=sources)
