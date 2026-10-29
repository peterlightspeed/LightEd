from lighted_ai.ingestion.pipeline import ingest_file
from lighted_ai.retrieval import Retriever


def _embedding_for_text(text: str) -> list[float]:
    lower = text.lower()
    if "vlan" in lower or "logical" in lower or "network" in lower:
        return [1.0, 0.0]
    if "firewall" in lower or "traffic" in lower or "security" in lower:
        return [0.0, 1.0]
    return [0.5, 0.5]


def test_ingestion_pipeline_indexes_chunks_for_retrieval(monkeypatch):
    lesson = (
        "A VLAN creates separate logical network segments. "
        "It keeps devices in one broadcast domain apart from another. "
        "A firewall filters traffic using security rules. "
        "The firewall allows or blocks packets based on policy."
    )

    monkeypatch.setattr(
        "lighted_ai.ingestion.pipeline.embed_batch",
        lambda texts, task_type="RETRIEVAL_DOCUMENT": [_embedding_for_text(text) for text in texts],
    )
    monkeypatch.setattr(
        "lighted_ai.retrieval.embed_batch",
        lambda texts, client=None, *, task_type="RETRIEVAL_DOCUMENT": [
            _embedding_for_text(text) for text in texts
        ],
    )
    monkeypatch.setattr(
        "lighted_ai.retrieval.embed_text",
        lambda text, client=None, *, task_type="RETRIEVAL_DOCUMENT": [1.0, 0.0],
    )

    ingested = ingest_file(lesson.encode("utf-8"), "lesson.txt")
    assert ingested.chunks
    assert any(chunk.chunk_level == "parent" for chunk in ingested.chunks)

    retriever = Retriever()
    retriever.add_ingested_documents([ingested])

    results = retriever.search("logical network segments", top_k=3)
    assert results
    top_match = results[0].document
    assert "VLAN" in top_match.text or "logical" in top_match.text.lower()
    assert top_match.metadata["source_name"] == "lesson.txt"
