
"""Validated weak-topic detection from learner attempt history."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Literal

# Tunable thresholds; scores are percentages in the range [0, 100].
WEAK_THRESHOLD = 60.0
CRITICAL_THRESHOLD = 40.0
STRONG_THRESHOLD = 80.0

TopicStatus = Literal["strong", "ok", "weak", "critical"]
Attempt = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class TopicStrength:
    topic: str
    avg_score: float
    attempts: int
    status: TopicStatus


def _status(avg: float) -> TopicStatus:
    """Classify an average score using the configured thresholds."""
    if avg < CRITICAL_THRESHOLD:
        return "critical"
    if avg < WEAK_THRESHOLD:
        return "weak"
    if avg < STRONG_THRESHOLD:
        return "ok"
    return "strong"


def _parse_attempt(
    attempt: Attempt,
    index: int,
) -> tuple[str, float]:
    """Validate and normalize one attempt."""
    topic_value = attempt.get("topic", "unknown")

    if not isinstance(topic_value, str):
        raise ValueError(
            f"Attempt at index {index}: topic must be a string."
        )

    topic = " ".join(topic_value.split()) or "unknown"

    score_value = attempt.get("score")

    # bool is a subclass of int, so explicitly reject it.
    if isinstance(score_value, bool) or not isinstance(score_value, Real):
        raise ValueError(
            f"Attempt at index {index}: score must be a numeric "
            "percentage between 0 and 100."
        )

    score = float(score_value)

    if not math.isfinite(score) or not 0.0 <= score <= 100.0:
        raise ValueError(
            f"Attempt at index {index}: score must be finite "
            "and between 0 and 100."
        )

    return topic, score


def detect_weak_topics(
    attempts: Sequence[Attempt],
) -> list[TopicStrength]:
    """Aggregate attempts by topic, sorted weakest-first.

    Each attempt must contain:
        {"topic": str, "score": number}

    Topic matching ignores case and repeated whitespace.
    Missing scores and invalid values raise ValueError rather
    than silently treating malformed attempts as zero.
    """
    # key -> [display name, running total, count]
    buckets: dict[str, list[object]] = {}

    for index, attempt in enumerate(attempts):
        if not isinstance(attempt, Mapping):
            raise ValueError(
                f"Attempt at index {index} must be a mapping."
            )

        topic, score = _parse_attempt(attempt, index)
        key = topic.casefold()

        if key not in buckets:
            buckets[key] = [topic, 0.0, 0]

        bucket = buckets[key]
        bucket[1] = float(bucket[1]) + score
        bucket[2] = int(bucket[2]) + 1

    results: list[TopicStrength] = []

    for display_topic, total, count in buckets.values():
        average = float(total) / int(count)

        results.append(
            TopicStrength(
                topic=str(display_topic),
                avg_score=round(average, 2),
                attempts=int(count),
                status=_status(average),
            )
        )

    results.sort(
        key=lambda result: (
            result.avg_score,
            result.topic.casefold(),
        )
    )
    return results


def weak_topic_names(
    attempts: Sequence[Attempt],
) -> list[str]:
    """Return topics classified as weak or critical."""
    return [
        result.topic
        for result in detect_weak_topics(attempts)
        if result.status in ("weak", "critical")
    ]
