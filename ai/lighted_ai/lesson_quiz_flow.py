"""End-to-end retrieval + quiz-generation flow for ingested lesson content."""
from __future__ import annotations

from typing import Any

from lighted_ai.ingestion.pipeline import IngestedDocument
from lighted_ai.quiz_generator import generate_quiz, student_facing_quiz
from lighted_ai.retrieval import Retriever


def generate_quiz_from_lesson(
    lesson: IngestedDocument | str,
    query: str,
    *,
    retriever: Retriever | None = None,
    num_questions: int = 2,
    title: str | None = None,
    topic_focus: str | None = None,
    attempts: Any = None,
    client: Any = None,
):
    """Retrieve the most relevant ingested lesson chunk, then generate a quiz."""
    if isinstance(lesson, IngestedDocument):
        source_text = lesson.content
        source_title = title or lesson.source_name
        if retriever is None:
            retriever = Retriever()
            retriever.add_ingested_documents([lesson])
    else:
        source_text = lesson
        source_title = title or "Lesson"
        if retriever is None:
            retriever = Retriever()

    if retriever is not None and query:
        matches = retriever.search(query, top_k=1)
        if matches:
            source_text = matches[0].document.text
            source_title = matches[0].document.metadata.get("title") or source_title

    quiz = generate_quiz(
        lesson_content=source_text,
        num_questions=num_questions,
        title=source_title,
        topic_focus=topic_focus,
        attempts=attempts,
        client=client,
    )
    return student_facing_quiz(quiz)
