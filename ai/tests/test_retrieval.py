import pytest

from lighted_ai import retrieval
from lighted_ai.config import settings
from lighted_ai.retrieval import Document, Retriever


def test_hybrid_search_uses_bm25_for_exact_terms(monkeypatch):
    documents = [
        Document("vlan", "VLANs separate devices into logical network segments."),
        Document("firewall", "Firewalls filter network traffic using rules."),
    ]
    monkeypatch.setattr(
        retrieval,
        "embed_batch",
        lambda texts: [[1.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        retrieval,
        "embed_text",
        lambda query, *, task_type: [1.0, 0.0],
    )

    retriever = Retriever()
    retriever.add_documents(documents)

    result = retriever.search("firewall", top_k=1)

    assert result[0].document.id == "firewall"
    assert result[0].score > 0


def test_hybrid_search_uses_faiss_for_semantic_matches(monkeypatch):
    documents = [
        Document("firewall", "Firewalls filter traffic using security rules."),
        Document("vlan", "VLANs create separate logical network segments."),
    ]
    embeddings = {
        documents[0].text: [0.0, 1.0],
        documents[1].text: [1.0, 0.0],
    }
    monkeypatch.setattr(
        retrieval,
        "embed_batch",
        lambda texts: [embeddings[text] for text in texts],
    )
    monkeypatch.setattr(
        retrieval,
        "embed_text",
        lambda query, *, task_type: [1.0, 0.0],
    )

    retriever = Retriever()
    retriever.add_documents(documents)

    result = retriever.search("isolate devices", top_k=1)

    assert result[0].document.id == "vlan"


def test_retriever_appends_documents_and_validates_top_k(monkeypatch):
    monkeypatch.setattr(
        retrieval,
        "embed_batch",
        lambda texts: [[1.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        retrieval,
        "embed_text",
        lambda query, *, task_type: [1.0, 0.0],
    )
    retriever = Retriever()
    retriever.add_documents([Document("first", "First course content.")])
    retriever.add_documents([Document("second", "Second course content.")])

    assert {
        result.document.id for result in retriever.search("course", top_k=2)
    } == {"first", "second"}
    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        retriever.search("course", top_k=0)


def test_retriever_rejects_mixed_embedding_config(monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "gemini")
    monkeypatch.setattr(settings, "embedding_model", "gemini-embedding-001")
    monkeypatch.setattr(settings, "gemini_embedding_dimensions", 2)
    monkeypatch.setattr(
        retrieval,
        "embed_batch",
        lambda texts: [[1.0, 0.0] for _ in texts],
    )
    retriever = Retriever()
    retriever.add_documents([Document("first", "First course content.")])

    monkeypatch.setattr(settings, "embedding_model", "another-model")
    with pytest.raises(RuntimeError, match="Embedding configuration changed"):
        retriever.add_documents([Document("second", "Second course content.")])

    assert [document.id for document in retriever._docs] == ["first"]


def test_failed_addition_preserves_existing_index(monkeypatch):
    monkeypatch.setattr(
        retrieval,
        "embed_batch",
        lambda texts: [[1.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        retrieval,
        "embed_text",
        lambda query, *, task_type: [1.0, 0.0],
    )
    retriever = Retriever()
    retriever.add_documents([Document("first", "First course content.")])

    def invalid_embeddings(texts):
        return [[0.0, 0.0] for _ in texts]

    monkeypatch.setattr(retrieval, "embed_batch", invalid_embeddings)
    with pytest.raises(ValueError, match="must not be zero vectors"):
        retriever.add_documents([Document("invalid", "Invalid addition.")])

    assert [result.document.id for result in retriever.search("course")] == [
        "first"
    ]
