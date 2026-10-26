"""Weak-topic detection from attempt history."""
from __future__ import annotations

from dataclasses import dataclass

# Tunable thresholds
WEAK_THRESHOLD = 60.0
CRITICAL_THRESHOLD = 40.0


@dataclass
class TopicStrength:
    topic: str
    avg_score: float
    attempts: int
    status: str  # "strong" | "ok" | "weak" | "critical"


def _status(avg: float) -> str:
    if avg < CRITICAL_THRESHOLD:
        return "critical"
    if avg < WEAK_THRESHOLD:
        return "weak"
    if avg < 80:
        return "ok"
    return "strong"


def detect_weak_topics(attempts: list[dict]) -> list[TopicStrength]:
    """Aggregate attempts (each: {"topic": str, "score": float}) per topic.

    Returns topics sorted weakest-first.
    """
    buckets: dict[str, list[float]] = {}
    for a in attempts:
        topic = a.get("topic", "unknown")
        buckets.setdefault(topic, []).append(float(a.get("score", 0)))

    results = [
        TopicStrength(
            topic=topic,
            avg_score=round(sum(scores) / len(scores), 2),
            attempts=len(scores),
            status=_status(sum(scores) / len(scores)),
        )
        for topic, scores in buckets.items()
    ]
    results.sort(key=lambda t: t.avg_score)
    return results


def weak_topic_names(attempts: list[dict]) -> list[str]:
    return [t.topic for t in detect_weak_topics(attempts) if t.status in ("weak", "critical")]
