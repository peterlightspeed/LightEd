"""Live Gemini integration tests; run with pytest -m integration -s."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from lighted_ai.config import AISettings, settings
from lighted_ai.retrieval import Document, Retriever


@pytest.mark.integration
def test_gemini_retrieves_relevant_document(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    project_settings = AISettings(_env_file=project_root / ".env")
    api_key = project_settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("Set GEMINI_API_KEY in the project .env or environment to run.")

    monkeypatch.setattr(settings, "gemini_api_key", api_key)
    monkeypatch.setattr(settings, "embedding_provider", "gemini")
    monkeypatch.setattr(settings, "embedding_model", project_settings.embedding_model)
    monkeypatch.setattr(
        settings,
        "gemini_embedding_dimensions",
        project_settings.gemini_embedding_dimensions,
    )

    documents = [
        Document("vlan", "A VLAN separates devices into logical network segments."),
        Document(
            "firewall",
            (
                "A firewall allows or blocks incoming and outgoing network traffic "
                "using security rules."
            ),
        ),
        Document(
            "subnet-mask",
            (
                "A subnet mask identifies which part of an IP address belongs to "
                "the network and which part identifies a host."
            ),
        ),
        Document(
            "encryption",
            (
                "Encryption protects information by transforming it into unreadable "
                "data that requires the correct key to decode."
            ),
        ),
    ]
    retriever = Retriever()
    retriever.add_documents(documents)

    cases = [
        (
            (
                "How can I put groups of devices on separate logical networks "
                "without changing physical cabling?"
            ),
            "vlan",
        ),
        (
            (
                "What controls whether incoming or outgoing traffic is allowed "
                "based on security rules?"
            ),
            "firewall",
        ),
        (
            "How do I tell which portion of an IP address identifies the network versus a host?",
            "subnet-mask",
        ),
        (
            "How can I keep information unreadable to someone who does not have the right key?",
            "encryption",
        ),
    ]

    for query, expected_id in cases:
     results = retriever.search(query, top_k=4)

     print(f"\nQUERY: {query}")
     for rank, result in enumerate(results, start=1):
        print(
            f"  Rank {rank}: "
            f"id={result.document.id!r}, "
            f"score={result.score:.10f}"
        )

     assert results[0].document.id == expected_id, (
        f"Query {query!r} ranked {results[0].document.id!r}; "
        f"expected {expected_id!r}"
    )
