"""Aggregated dashboard payloads.

The frontend renders these directly, so each response is shaped for a screen
rather than exposing raw tables.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.quiz import Quiz
from app.models.topic import Topic
from app.models.user import User
from app.schemas.user import UserOut
from app.services.learning import average_score, completed_lesson_ids

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

ACCENTS = ["blue", "violet", "amber", "emerald", "rose"]


def _course_cards(db: Session, user_id: int) -> list[dict]:
    enrolled_ids = list(
        db.scalars(select(Enrollment.course_id).where(Enrollment.user_id == user_id)).all()
    )
    if not enrolled_ids:
        return []
    courses = db.scalars(
        select(Course)
        .options(selectinload(Course.topics).selectinload(Topic.lessons))
        .where(Course.id.in_(enrolled_ids))
    ).all()
    completed = completed_lesson_ids(db, user_id)
    cards = []
    for c in courses:
        lessons = [l for t in c.topics for l in t.lessons]
        done = len([l for l in lessons if l.id in completed])
        cards.append(
            {
                "id": c.id,
                "title": c.title,
                "subject": c.subject,
                "level": c.level,
                "accent": c.accent,
                "lesson_count": len(lessons),
                "lessons_completed": done,
                "progress": round((done / len(lessons)) * 100) if lessons else 0,
            }
        )
    return cards


@router.get("/student")
def student_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cards = _course_cards(db, user.id)
    completed = completed_lesson_ids(db, user.id)
    total_lessons = sum(c["lesson_count"] for c in cards)

    # Continue learning = first incomplete lesson in the least-complete course.
    continue_learning = None
    for card in sorted(cards, key=lambda c: c["progress"]):
        course = db.scalar(
            select(Course)
            .options(selectinload(Course.topics).selectinload(Topic.lessons))
            .where(Course.id == card["id"])
        )
        for topic in sorted(course.topics, key=lambda t: t.order_index):
            for lesson in sorted(topic.lessons, key=lambda l: l.order_index):
                if lesson.id not in completed:
                    continue_learning = {
                        "course_id": course.id,
                        "course_title": course.title,
                        "lesson_id": lesson.id,
                        "lesson_title": lesson.title,
                        "topic_title": topic.title,
                        "progress": card["progress"],
                    }
                    break
            if continue_learning:
                break
        if continue_learning:
            break

    # Focus areas: mastery per course (quiz average blended with completion).
    focus_areas = []
    for card in cards[:3]:
        quiz_avg = db.scalar(
            select(func.avg(Attempt.score))
            .join(Quiz, Attempt.quiz_id == Quiz.id)
            .join(Lesson, Quiz.lesson_id == Lesson.id)
            .join(Topic, Lesson.topic_id == Topic.id)
            .where(Topic.course_id == card["id"], Attempt.user_id == user.id)
        )
        mastery = round((float(quiz_avg) * 0.7 + card["progress"] * 0.3)) if quiz_avg else card["progress"]
        focus_areas.append(
            {"course_id": card["id"], "label": card["subject"], "mastery": mastery}
        )

    # Recommendations: courses not yet enrolled, newest first.
    enrolled_ids = {c["id"] for c in cards}
    available = db.scalars(select(Course).where(Course.published.is_(True))).all()
    recommendations = [
        {
            "course_id": c.id,
            "title": c.title,
            "subject": c.subject,
            "level": c.level,
            "accent": c.accent,
            "reason": "Popular with students in your year",
        }
        for c in available
        if c.id not in enrolled_ids
    ][:3]

    attempts = db.execute(
        select(Attempt, Quiz, Lesson)
        .join(Quiz, Attempt.quiz_id == Quiz.id)
        .join(Lesson, Quiz.lesson_id == Lesson.id)
        .where(Attempt.user_id == user.id)
        .order_by(Attempt.created_at.desc())
        .limit(5)
    ).all()

    # Weekly activity (last 7 days) from lesson completions.
    since = datetime.now(timezone.utc) - timedelta(days=6)
    rows = db.execute(
        select(Progress.completed_at).where(
            Progress.user_id == user.id,
            Progress.completed.is_(True),
            Progress.completed_at >= since,
        )
    ).all()
    counts: dict[str, int] = {}
    for (ts,) in rows:
        if ts:
            counts[ts.strftime("%a")] = counts.get(ts.strftime("%a"), 0) + 1
    weekly = [
        {"day": (datetime.now(timezone.utc) - timedelta(days=6 - i)).strftime("%a"),
         "lessons": counts.get((datetime.now(timezone.utc) - timedelta(days=6 - i)).strftime("%a"), 0)}
        for i in range(7)
    ]

    return {
        "user": UserOut.model_validate(user).model_dump(),
        "stats": {
            "enrolled_courses": len(cards),
            "lessons_completed": len(completed),
            "lessons_total": total_lessons,
            "avg_score": average_score(db, user.id),
            "streak_days": sum(1 for d in weekly if d["lessons"] > 0),
        },
        "continue_learning": continue_learning,
        "courses": cards,
        "focus_areas": focus_areas,
        "recommendations": recommendations,
        "recent_attempts": [
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "quiz_title": q.title,
                "lesson_title": l.title,
                "score": a.score,
                "created_at": a.created_at,
            }
            for a, q, l in attempts
        ],
        "weekly_activity": weekly,
    }


@router.get("/teacher")
def teacher_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    course_stmt = select(Course).options(selectinload(Course.topics).selectinload(Topic.lessons))
    if user.role != "admin":
        course_stmt = course_stmt.where(Course.owner_id == user.id)
    courses = db.scalars(course_stmt).all()

    # Only students enrolled in THIS teacher's courses (admins: all enrolled students).
    enrolled_ids = {e.user_id for e in db.scalars(select(Enrollment).where(Enrollment.course_id.in_([c.id for c in courses] or [-1])))}
    students = db.scalars(select(User).where(User.id.in_(enrolled_ids or {-1}), User.role == "student")).all()
    student_rows = []
    for s in students:
        avg = average_score(db, s.id)
        completed = len(completed_lesson_ids(db, s.id))
        student_rows.append(
            {
                "id": s.id,
                "name": s.full_name,
                "email": s.email,
                "avg_score": avg,
                "lessons_completed": completed,
                "status": "at_risk" if avg and avg < 60 else "on_track",
            }
        )

    course_rows = []
    for c in courses:
        lesson_ids = [l.id for t in c.topics for l in t.lessons]
        enrolled = db.scalar(
            select(func.count()).select_from(Enrollment).where(Enrollment.course_id == c.id)
        ) or 0
        # Average completion across enrolled students.
        progress_values = []
        for e in db.scalars(select(Enrollment).where(Enrollment.course_id == c.id)).all():
            done = len(completed_lesson_ids(db, e.user_id).intersection(lesson_ids))
            progress_values.append((done / len(lesson_ids)) * 100 if lesson_ids else 0)
        course_rows.append(
            {
                "id": c.id,
                "title": c.title,
                "subject": c.subject,
                "accent": c.accent,
                "students": enrolled,
                "lessons": len(lesson_ids),
                "avg_progress": round(sum(progress_values) / len(progress_values)) if progress_values else 0,
            }
        )

    overall_avg = db.scalar(select(func.avg(Attempt.score))) or 0
    return {
        "user": UserOut.model_validate(user).model_dump(),
        "stats": {
            "total_students": len(students),
            "active_courses": len(courses),
            "avg_score": round(float(overall_avg), 1),
            "at_risk": len([s for s in student_rows if s["status"] == "at_risk"]),
        },
        "courses": course_rows,
        "students": sorted(student_rows, key=lambda s: (s["status"] != "at_risk", s["avg_score"]))[:6],
    }


@router.get("/admin")
def admin_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    courses = db.scalars(select(Course)).all()
    attempts = db.scalar(select(func.count()).select_from(Attempt)) or 0
    return {
        "stats": {
            "users": len(users),
            "students": len([u for u in users if u.role == "student"]),
            "teachers": len([u for u in users if u.role == "teacher"]),
            "courses": len(courses),
            "attempts": attempts,
        },
        "users": [UserOut.model_validate(u).model_dump() for u in users],
        "courses": [
            {"id": c.id, "title": c.title, "subject": c.subject, "published": c.published}
            for c in courses
        ],
    }
