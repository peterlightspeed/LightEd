from lighted_ai.retrieval import Document, Retriever
from lighted_ai.tutor import answer_question


class FakeClient:
    def generate(self, prompt, system=None):
        return "A VLAN separates devices into logical network segments."


def test_answer_question_returns_grounded_answer_and_frontend_sources(monkeypatch):
    documents = [
        Document(
            "vlan",
            "A VLAN separates devices into logical network segments.",
            metadata={"title": "VLAN Basics", "source_type": "text", "location": "lesson.txt"},
        ),
        Document(
            "firewall",
            "A firewall filters incoming and outgoing traffic using security rules.",
            metadata={"title": "Firewall Basics", "source_type": "text", "location": "lesson.txt"},
        ),
    ]

    embeddings = {
        "A VLAN separates devices into logical network segments.": [1.0, 0.0],
        "A firewall filters incoming and outgoing traffic using security rules.": [0.0, 1.0],
    }

    monkeypatch.setattr(
        "lighted_ai.retrieval.embed_batch",
        lambda texts, client=None, *, task_type="RETRIEVAL_DOCUMENT": [embeddings[text] for text in texts],
    )
    monkeypatch.setattr(
        "lighted_ai.retrieval.embed_text",
        lambda text, client=None, *, task_type="RETRIEVAL_DOCUMENT": [1.0, 0.0] if "VLAN" in text.upper() else [0.0, 1.0],
    )

    retriever = Retriever()
    retriever.add_documents(documents)

    result = answer_question(
        "What does a VLAN do?",
        retriever=retriever,
        client=FakeClient(),
    )

    assert "VLAN" in result.answer
    assert result.sources
    assert result.sources[0]["title"] == "VLAN Basics"
    assert result.frontend_sources[0]["snippet"]


def test_answer_question_handles_no_context_gracefully(monkeypatch):
    retriever = Retriever()

    result = answer_question("What is a network?", retriever=retriever)

    assert "I couldn't find enough course material" in result.answer
    assert result.sources == []
