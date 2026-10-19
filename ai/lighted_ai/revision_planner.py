"""Revision planner: turn weak topics into a prioritized study schedule."""
from __future__ import annotations

from dataclasses import dataclass

from lighted_ai.weak_topics import TopicStrength, detect_weak_topics


@dataclass
class RevisionItem:
    topic: str
    priority: int  # 1 = highest
    reason: str
    suggested_minutes: int


def build_revision_plan(attempts: list[dict], days: int = 7) -> list[RevisionItem]:
    """Create a prioritized revision plan from attempt history.

    Weakest topics get the highest priority and the most time.
    """
    strengths: list[TopicStrength] = detect_weak_topics(attempts)
    plan: list[RevisionItem] = []

    for i, t in enumerate(strengths):
        if t.status == "strong":
            continue
        minutes = 45 if t.status == "critical" else 30 if t.status == "weak" else 15
        plan.append(
            RevisionItem(
                topic=t.topic,
                priority=i + 1,
                reason=f"Average score {t.avg_score}% ({t.status})",
                suggested_minutes=minutes,
            )
        )

    if not plan:
        plan.append(
            RevisionItem(
                topic="All topics",
                priority=1,
                reason="No weak topics detected — do light review to maintain mastery.",
                suggested_minutes=20,
            )
        )
    return plan


def plan_as_schedule(attempts: list[dict], days: int = 7) -> list[dict]:
    """Distribute revision items across the next `days` days."""
    plan = build_revision_plan(attempts, days=days)
    schedule: list[dict] = []
    for day in range(1, days + 1):
        item = plan[(day - 1) % len(plan)]
        schedule.append(
            {
                "day": day,
                "topic": item.topic,
                "minutes": item.suggested_minutes,
                "reason": item.reason,
            }
        )
    return schedule
