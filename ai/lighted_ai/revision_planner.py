
"""Revision planner: prioritize weak topics and schedule study sessions."""
from __future__ import annotations

from dataclasses import dataclass

from lighted_ai.weak_topics import TopicStrength, detect_weak_topics


@dataclass(frozen=True, slots=True)
class RevisionItem:
    topic: str
    priority: int
    reason: str
    suggested_minutes: int


def _validate_days(days: int) -> int:
    if isinstance(days, bool) or not isinstance(days, int):
        raise TypeError("days must be an integer.")
    if not 1 <= days <= 365:
        raise ValueError("days must be between 1 and 365.")
    return days


def build_revision_plan(
    attempts: list[dict],
    days: int = 7,
) -> list[RevisionItem]:
    """Build a prioritized list of revision topics.

    The days argument is retained for API compatibility and validated.
    It controls schedule length, not the number of unique weak topics.
    """
    _validate_days(days)
    strengths: list[TopicStrength] = detect_weak_topics(attempts)
    plan: list[RevisionItem] = []

    for strength in strengths:
        if strength.status == "strong":
            continue

        minutes = {
            "critical": 45,
            "weak": 30,
            "ok": 15,
        }.get(strength.status, 15)

        plan.append(
            RevisionItem(
                topic=strength.topic,
                priority=len(plan) + 1,
                reason=f"Average score {strength.avg_score:.2f}% ({strength.status})",
                suggested_minutes=minutes,
            )
        )

    if not plan:
        plan.append(
            RevisionItem(
                topic="All topics",
                priority=1,
                reason=(
                    "No weak topics detected — light review can help "
                    "maintain mastery."
                ),
                suggested_minutes=20,
            )
        )

    return plan


def plan_as_schedule(
    attempts: list[dict],
    days: int = 7,
) -> list[dict]:
    """Distribute revision items across the requested number of days."""
    days = _validate_days(days)
    plan = build_revision_plan(attempts, days=days)

    return [
        {
            "day": day,
            "topic": plan[(day - 1) % len(plan)].topic,
            "minutes": plan[(day - 1) % len(plan)].suggested_minutes,
            "reason": plan[(day - 1) % len(plan)].reason,
        }
        for day in range(1, days + 1)
    ]
