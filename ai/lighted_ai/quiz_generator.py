"""Generate quiz questions from lesson content."""
from __future__ import annotations

import json
import re

from lighted_ai.gemini_client import GeminiClient

QUIZ_PROMPT = """You are a quiz generator for an education platform.
Create {n} multiple-choice questions based ONLY on the lesson below.
Return STRICT JSON: a list of objects with keys:
  "prompt" (string), "options" (list of 4 strings), "answer_index" (0-3).

Lesson title: {title}
Lesson content:
{content}
"""


def _parse_json(text: str) -> list[dict]:
    """Extract a JSON array from a model response, tolerating code fences."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def generate_quiz(
    lesson_content: str,
    num_questions: int = 5,
    title: str = "",
    client: GeminiClient | None = None,
) -> list[dict]:
    prompt = QUIZ_PROMPT.format(n=num_questions, title=title, content=lesson_content)
    try:
        raw = (client or GeminiClient()).generate(prompt)
        questions = _parse_json(raw)
        if questions:
            return questions
    except Exception:  # noqa: BLE001
        pass

    # Deterministic fallback so the endpoint always returns something usable.
    return [
        {
            "prompt": f"Question {i + 1} about {title or 'this lesson'}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer_index": 0,
        }
        for i in range(num_questions)
    ]
