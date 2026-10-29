from lighted_ai.ingestion.pipeline import ingest_file
from lighted_ai.lesson_quiz_flow import generate_quiz_from_lesson


class FakeClient:
    def generate_text(self, prompt, **kwargs):
        if "QUIZ_TO_VERIFY" in prompt:
            return '{"results": [{"question_index": 0, "supported": true, "answer_correct": true, "uniquely_correct": true, "answerable_from_lesson": true, "explanation_supported": true, "confidence": 0.93, "evidence_quote": "A VLAN separates devices into logical network segments.", "reason": "The lesson explicitly states this."}, {"question_index": 1, "supported": true, "answer_correct": true, "uniquely_correct": true, "answerable_from_lesson": true, "explanation_supported": true, "confidence": 0.92, "evidence_quote": "logical network segments", "reason": "The evidence quote matches the lesson."}]}'
        return '[{"question": "What is a VLAN?", "options": ["A logical grouping of devices", "A firewall rule set", "A cable type", "A routing protocol"], "answer_index": 0, "explanation": "A VLAN separates devices into logical network segments."}, {"question": "What does a VLAN change?", "options": ["Logical grouping of devices", "The physical network cable", "The IP table", "The router vendor"], "answer_index": 0, "explanation": "A VLAN changes logical segmentation without changing physical wiring."}]'


def test_generate_quiz_from_lesson_uses_retrieved_chunk(monkeypatch):
    lesson = ingest_file(
        b"A VLAN separates devices into logical network segments. A firewall filters traffic using rules.",
        "lesson.txt",
    )

    monkeypatch.setattr(
        "lighted_ai.ingestion.pipeline.embed_batch",
        lambda texts, task_type="RETRIEVAL_DOCUMENT": [[1.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        "lighted_ai.retrieval.embed_batch",
        lambda texts, client=None, *, task_type="RETRIEVAL_DOCUMENT": [[1.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        "lighted_ai.retrieval.embed_text",
        lambda text, client=None, *, task_type="RETRIEVAL_DOCUMENT": [1.0, 0.0],
    )

    result = generate_quiz_from_lesson(
        lesson=lesson,
        query="logical network segments",
        num_questions=2,
        client=FakeClient(),
    )

    assert len(result) == 2
    assert result[0]["question"]
    assert "_verification" not in result[0]
    assert result[0]["answer_index"] in {0, 1, 2, 3}
