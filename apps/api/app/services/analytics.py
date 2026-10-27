"""Learning analytics: topic accuracy, transparent rule-based risk score, study planner.

Rules are deliberately simple and explainable (see PDF §10): a teacher can read
exactly WHY a student is flagged.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.quiz import Quiz
from app.models.topic import Topic

WEAK_THRESHOLD = 60.0  # topic accuracy below this => weak (PDF O4)


def topic_scores(db: Session, user_id: int, course_ids: list[int] | None = None) -> list[dict]:
    """Average quiz score per topic for one student (weakest first)."""
    stmt = (
        select(Topic.id, Topic.title, Topic.course_id, func.avg(Attempt.score), func.count(Attempt.id))
        .select_from(Attempt)
        .join(Quiz, Quiz.id == Attempt.quiz_id)
        .join(Lesson, Lesson.id == Quiz.lesson_id)
        .join(Topic, Topic.id == Lesson.topic_id)
        .where(Attempt.user_id == user_id)
        .group_by(Topic.id, Topic.title, Topic.course_id)
    )
    if course_ids is not None:
        stmt = stmt.where(Topic.course_id.in_(course_ids))
    rows = db.execute(stmt).all()
    out = [
        {"topic_id": r[0], "topic": r[1], "course_id": r[2], "score": round(float(r[3])), "attempts": r[4]}
        for r in rows
    ]
    return sorted(out, key=lambda x: x["score"])


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def student_metrics(db: Session, user_id: int, course_ids: list[int]) -> dict:
    """Raw numbers used for the risk score and the teacher views."""
    attempts = db.execute(
        select(Attempt.score, Attempt.created_at)
        .join(Quiz, Quiz.id == Attempt.quiz_id)
        .join(Lesson, Lesson.id == Quiz.lesson_id)
        .join(Topic, Topic.id == Lesson.topic_id)
        .where(Attempt.user_id == user_id, Topic.course_id.in_(course_ids))
        .order_by(Attempt.created_at, Attempt.id)
    ).all()
    scores = [float(a[0]) for a in attempts]

    lesson_ids = list(
        db.scalars(select(Lesson.id).join(Topic, Topic.id == Lesson.topic_id).where(Topic.course_id.in_(course_ids)))
    )
    done_rows = db.execute(
        select(Progress.lesson_id, Progress.completed_at).where(
            Progress.user_id == user_id, Progress.completed.is_(True), Progress.lesson_id.in_(lesson_ids or [-1])
        )
    ).all()

    stamps = [_as_utc(a[1]) for a in attempts if a[1]] + [_as_utc(d[1]) for d in done_rows if d[1]]
    last_active = max(stamps) if stamps else None
    return {
        "avg_score": round(sum(scores) / len(scores)) if scores else None,
        "attempts": len(scores),
        "recent_avg": round(sum(scores[-3:]) / len(scores[-3:])) if scores else None,
        "earlier_avg": round(sum(scores[:-3]) / len(scores[:-3])) if len(scores) > 3 else None,
        "lessons_total": len(lesson_ids),
        "lessons_completed": len(done_rows),
        "completion": round(len(done_rows) / len(lesson_ids) * 100) if lesson_ids else 0,
        "last_active": last_active,
    }


def risk_from_metrics(m: dict) -> dict:
    """Transparent rule-based risk (PDF: 'simple risk score' for the MVP; ML later).

    Points: low average (+40/+20), falling trend (+20), low completion (+20),
    inactivity (+20), no quiz data yet (+10). Band: >=50 high, >=25 medium, else low.
    """
    points, factors = 0, []
    avg = m["avg_score"]
    if avg is None:
        points += 10
        factors.append("No quiz attempts yet")
    elif avg < 60:
        points += 40
        factors.append(f"Average quiz score is {avg}% (below 60%)")
    elif avg < 70:
        points += 20
        factors.append(f"Average quiz score is only {avg}%")
    if m["earlier_avg"] is not None and m["recent_avg"] is not None and m["recent_avg"] <= m["earlier_avg"] - 10:
        points += 20
        factors.append(f"Recent scores dropped ({m['earlier_avg']}% → {m['recent_avg']}%)")
    if m["lessons_total"] and m["completion"] < 30:
        points += 20
        factors.append(f"Only {m['completion']}% of lessons completed")
    la = m["last_active"]
    if la and (datetime.now(timezone.utc) - la) > timedelta(days=14):
        points += 20
        factors.append("No activity for over 14 days")
    band = "high" if points >= 50 else "medium" if points >= 25 else "low"
    return {"band": band, "score": min(points, 100), "factors": factors}


def enrolled_course_ids(db: Session, user_id: int, only_owner_id: int | None = None) -> list[int]:
    stmt = select(Enrollment.course_id).where(Enrollment.user_id == user_id)
    if only_owner_id is not None:
        stmt = stmt.join(Course, Course.id == Enrollment.course_id).where(Course.owner_id == only_owner_id)
    return list(db.scalars(stmt))


# ------------------------------------------------------------------ study planner
def build_plan(db: Session, user_id: int, course: Course, exam_date: date, minutes_per_day: int) -> dict:
    """Revision schedule: weak topics first (revise), then unfinished lessons in order.

    Greedy fill of each day up to `minutes_per_day`. Anything that doesn't fit before
    the exam is reported as `unscheduled` so the student can raise daily time.
    """
    today = date.today()
    days_available = (exam_date - today).days  # exam day itself is kept free
    if days_available < 1:
        raise ValueError("Exam date must be at least tomorrow")
    days_available = min(days_available, 60)

    topics = list(db.scalars(select(Topic).where(Topic.course_id == course.id).order_by(Topic.order_index, Topic.id)))
    scores = {t["topic_id"]: t for t in topic_scores(db, user_id, [course.id])}
    done = set(
        db.scalars(select(Progress.lesson_id).where(Progress.user_id == user_id, Progress.completed.is_(True)))
    )

    revise, learn = [], []
    weak_names = []
    for t in topics:
        lessons = list(db.scalars(select(Lesson).where(Lesson.topic_id == t.id).order_by(Lesson.order_index, Lesson.id)))
        sc = scores.get(t.id)
        is_weak = sc is not None and sc["score"] < WEAK_THRESHOLD
        if is_weak:
            weak_names.append(t.title)
        for l in lessons:
            minutes = (l.duration_minutes or 10) + 5  # +5 min for the quiz
            if is_weak:
                revise.append({"lesson_id": l.id, "title": l.title, "topic": t.title, "minutes": minutes,
                               "kind": "revise", "reason": f"Weak topic ({sc['score']}% accuracy)"})
            elif l.id not in done:
                learn.append({"lesson_id": l.id, "title": l.title, "topic": t.title, "minutes": minutes,
                              "kind": "learn", "reason": "Not completed yet"})

    queue = revise + learn
    days = [{"date": (today + timedelta(days=i + 1)).isoformat(), "total_minutes": 0, "items": []} for i in range(days_available)]
    di = 0
    unscheduled = 0
    for item in queue:
        while di < len(days) and days[di]["total_minutes"] + item["minutes"] > minutes_per_day and days[di]["items"]:
            di += 1
        if di >= len(days):
            unscheduled += 1
            continue
        days[di]["items"].append(item)
        days[di]["total_minutes"] += item["minutes"]
    days = [d for d in days if d["items"]]
    return {
        "course": {"id": course.id, "title": course.title},
        "exam_date": exam_date.isoformat(),
        "minutes_per_day": minutes_per_day,
        "weak_topics": weak_names,
        "total_minutes": sum(d["total_minutes"] for d in days),
        "unscheduled": unscheduled,
        "days": days,
    }
