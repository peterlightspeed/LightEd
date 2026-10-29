import pytest

from lighted_ai.quiz_generator import (
    QuizGenerationError,
    generate_quiz,
    student_facing_quiz,
    validate_quiz,
)


VALID_QUESTION = {
    "question": "Which statement correctly describes a VLAN?",
    "options": [
        "It groups devices into logical network segments.",
        "It changes the physical cable layout.",
        "It acts as a firewall policy engine.",
        "It encrypts all traffic automatically.",
    ],
    "answer_index": 0,
    "explanation": "A VLAN separates devices logically without changing the physical cabling.",
}


def test_validate_quiz_accepts_valid_schema():
    questions = [VALID_QUESTION]
    cleaned = validate_quiz(questions)

    assert len(cleaned) == 1
    assert cleaned[0]["question"] == VALID_QUESTION["question"]
    assert cleaned[0]["answer_index"] == 0


def test_validate_quiz_rejects_invalid_question_shape():
    invalid = [{
        "question": "Which option is valid?",
        "options": ["Only one option"],
        "answer_index": 4,
        "explanation": "This is invalid.",
    }]

    with pytest.raises(ValueError):
        validate_quiz(invalid)


def test_generate_quiz_raises_when_model_returns_bad_json():
    class FakeClient:
        def generate_text(self, prompt, **kwargs):
            return "not valid json"

    with pytest.raises(QuizGenerationError):
        generate_quiz(
            "A VLAN separates devices into logical network segments.",
            num_questions=2,
            title="VLANs",
            client=FakeClient(),
        )


def test_generate_quiz_returns_verified_questions_when_valid():
    class FakeClient:
        def generate_text(self, prompt, **kwargs):
            if "QUIZ_TO_VERIFY" in prompt:
                return '{"results": [{"question_index": 0, "supported": true, "answer_correct": true, "uniquely_correct": true, "answerable_from_lesson": true, "explanation_supported": true, "confidence": 0.95, "evidence_quote": "A VLAN separates devices into logical network segments.", "reason": "The lesson states this directly."}, {"question_index": 1, "supported": true, "answer_correct": true, "uniquely_correct": true, "answerable_from_lesson": true, "explanation_supported": true, "confidence": 0.94, "evidence_quote": "logical network segments", "reason": "The evidence quote matches the lesson."}]}'
            return '[{"question": "What is a VLAN?", "options": ["A logical grouping of devices", "A type of firewall", "A routing protocol", "A cable type"], "answer_index": 0, "explanation": "A VLAN separates devices into logical network segments without changing physical cabling."}, {"question": "What does a VLAN change?", "options": ["The logical grouping of devices", "The physical cable installation", "The IP address range", "The router model"], "answer_index": 0, "explanation": "A VLAN changes logical segmentation rather than the physical wiring."}]'

    result = generate_quiz(
        "A VLAN separates devices into logical network segments.",
        num_questions=2,
        title="VLANs",
        client=FakeClient(),
    )

    assert len(result) == 2
    assert result[0]["question"].startswith("What is a VLAN")
    assert "_verification" in result[0]

    public = student_facing_quiz(result)
    assert public[0]["question"] == result[0]["question"]
    assert "_verification" not in public[0]


def test_generate_quiz_prioritizes_weak_topic_focus():
    attempts = [{"topic": "Subnetting", "score": 35}, {"topic": "Routing", "score": 80}]

    class FakeClient:
        def generate_text(self, prompt, **kwargs):
            if "QUIZ_TO_VERIFY" in prompt:
                return '{"results": [{"question_index": 0, "supported": true, "answer_correct": true, "uniquely_correct": true, "answerable_from_lesson": true, "explanation_supported": true, "confidence": 0.9, "evidence_quote": "Subnet masks identify the network portion of an IP address.", "reason": "It directly supports the answer."}]}'
            return '[{"question": "What does a subnet mask identify?", "options": ["The network portion of an IP address", "The firewall rule set", "The router hardware", "The physical cable type"], "answer_index": 0, "explanation": "A subnet mask distinguishes the network portion from the host portion."}]'

    result = generate_quiz(
        "Subnet masks identify the network portion of an IP address.",
        num_questions=1,
        title="Subnetting",
        attempts=attempts,
        client=FakeClient(),
    )

    assert len(result) == 1
    question_text = result[0]["question"].lower()
    assert "subnet" in question_text or "network" in question_text
