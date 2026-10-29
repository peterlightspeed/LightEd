"""2-minute end-to-end demo for the LightEd AI workflow.

Flow:
1. Ingest a lesson file into the ingestion pipeline
2. Build semantic parent/child chunks and index them in the retriever
3. Search for the best-matching lesson chunk
4. Generate a lesson-grounded quiz from the retrieved chunk

Use the real Gemini client when a key is configured; otherwise the script falls
back to a deterministic local demo client so the full flow can still be shown.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from lighted_ai.config import get_api_key
from lighted_ai.ingestion.pipeline import ingest_file
from lighted_ai.lesson_quiz_flow import generate_quiz_from_lesson
from lighted_ai.provider_router import ProviderRouter, ProviderFallbackError
from lighted_ai.retrieval import Retriever


def _demo_lesson_text() -> str:
    return (
        "A VLAN separates devices into logical network segments. "
        "This keeps traffic and broadcast domains organized without changing physical cabling. "
        "A firewall filters incoming and outgoing network traffic using security rules. "
        "It allows or blocks traffic based on policy, helping protect a network from unwanted access."
    )


class DemoClient:
    """Minimal deterministic client for local demos when Gemini is unavailable."""

    def __init__(self, lesson_text: str) -> None:
        self.lesson_text = lesson_text

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        if "QUIZ_TO_VERIFY" in prompt:
            return json.dumps(
                {
                    "results": [
                        {
                            "question_index": 0,
                            "supported": True,
                            "answer_correct": True,
                            "uniquely_correct": True,
                            "answerable_from_lesson": True,
                            "explanation_supported": True,
                            "confidence": 0.94,
                            "evidence_quote": "A VLAN separates devices into logical network segments.",
                            "reason": "The lesson explicitly states this fact.",
                        },
                        {
                            "question_index": 1,
                            "supported": True,
                            "answer_correct": True,
                            "uniquely_correct": True,
                            "answerable_from_lesson": True,
                            "explanation_supported": True,
                            "confidence": 0.92,
                            "evidence_quote": "A firewall filters incoming and outgoing network traffic using security rules.",
                            "reason": "This exact behaviour is described in the lesson.",
                        },
                    ]
                }
            )

        return json.dumps(
            [
                {
                    "question": "What does a VLAN do?",
                    "options": [
                        "It groups devices into logical network segments",
                        "It changes the physical wiring",
                        "It replaces the firewall",
                        "It encrypts all traffic automatically",
                    ],
                    "answer_index": 0,
                    "explanation": "A VLAN separates devices into logical network segments without changing the physical cable layout.",
                },
                {
                    "question": "What is a firewall responsible for?",
                    "options": [
                        "Filtering incoming and outgoing traffic using rules",
                        "Changing the network IP range",
                        "Routing between VLANs without rules",
                        "Creating a logical broadcast segment",
                    ],
                    "answer_index": 0,
                    "explanation": "The lesson states that a firewall filters incoming and outgoing network traffic using security rules.",
                },
            ]
        )


def run_demo(*, use_real: bool | None = None) -> None:
    lesson_text = _demo_lesson_text()
    ingested = ingest_file(lesson_text.encode("utf-8"), "network_basics.txt")
    retriever = Retriever()
    retriever.add_ingested_documents([ingested])

    query = "How do VLANs keep devices in separate logical groups?"
    matches = retriever.search(query, top_k=1)
    if not matches:
        raise RuntimeError("No retrieval matches were produced by the demo lesson.")

    best_match = matches[0].document
    api_key = get_api_key()
    resolved_use_real = bool(api_key) if use_real is None else bool(use_real and api_key)

    print("=== 1) INGESTION ===")
    print(f"source: {ingested.source_name}")
    print(f"chunks: {len(ingested.chunks)} total ({sum(c.chunk_level == 'parent' for c in ingested.chunks)} parent, {sum(c.chunk_level == 'child' for c in ingested.chunks)} child)")
    print(f"first child preview: {ingested.chunks[0].content[:120]}...")

    print("\n=== 2) RETRIEVAL ===")
    print(f"query: {query}")
    print(f"best match: {best_match.id}")
    print(best_match.text)

    print("\n=== 3) QUIZ GENERATION ===")
    client: Any
    if resolved_use_real:
        try:
            client = ProviderRouter()
            print("Using routed provider model (Gemini first, Grok fallback).")
        except Exception as exc:  # pragma: no cover - provider/runtime fallback
            print(f"Using local demo client (real provider unavailable: {exc}).")
            client = DemoClient(best_match.text)
    else:
        client = DemoClient(best_match.text)
        if api_key:
            print("Using local demo client (provider model unavailable in this runtime).")
        else:
            print("Using local demo client (provider keys not configured).")

    try:
        quiz = generate_quiz_from_lesson(
            lesson=ingested,
            query=query,
            retriever=retriever,
            num_questions=2,
            client=client,
        )
    except Exception as exc:  # pragma: no cover - provider/runtime fallback
        if api_key:
            print(f"Using local demo client after provider failure: {exc}")
        else:
            print("Using local demo client because the Gemini provider is unavailable.")
        client = DemoClient(best_match.text)
        quiz = generate_quiz_from_lesson(
            lesson=ingested,
            query=query,
            retriever=retriever,
            num_questions=2,
            client=client,
        )

    for idx, item in enumerate(quiz, start=1):
        print(f"Q{idx}: {item['question']}")
        for option_index, option in enumerate(item["options"]):
            marker = "*" if option_index == item["answer_index"] else " "
            print(f"  {marker} {option_index}: {option}")
        print(f"  explanation: {item['explanation']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ingest → retrieve → quiz demo workflow.")
    parser.add_argument(
        "--real",
        action="store_true",
        default=None,
        help="Use the configured Gemini API if a key is available; otherwise falls back to the demo client.",
    )
    args = parser.parse_args()
    run_demo(use_real=args.real)
