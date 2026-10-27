"""Teacher/admin views of students: roster, risk, and per-student detail.

Scope: a teacher sees ONLY students enrolled in courses they own. Admins see everyone.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.topic import Topic
from app.models.user import User
from app.services.analytics import enrolled_course_ids, risk_from_metrics, student_metrics, topic_scores

router = APIRouter(prefix="/teacher", tags=["teacher"])


def _scope_owner(user: User) -> int | None:
    return None if user.role == "admin" else user.id


def _student_ids(db: Session, user: User) -> list[int]:
    stmt = select(Enrollment.user_id).distinct()
    if user.role != "admin":
        stmt = stmt.join(Course, Course.id == Enrollment.course_id).where(Course.owner_id == user.id)
    return list(db.scalars(stmt))


def student_row(db: Session, student: User, owner_id: int | None) -> dict:
    cids = enrolled_course_ids(db, student.id, owner_id)
    m = student_metrics(db, student.id, cids) if cids else student_metrics(db, student.id, [-1])
    titles = list(db.scalars(select(Course.title).where(Course.id.in_(cids)))) if cids else []
    return {
        "id": student.id,
        "name": student.full_name,
        "email": student.email,
        "courses": titles,
        "avg_score": m["avg_score"],
        "attempts": m["attempts"],
        "completion": m["completion"],
        "lessons_completed": m["lessons_completed"],
        "last_active": m["last_active"].isoformat() if m["last_active"] else None,
        "risk": risk_from_metrics(m),
    }


@router.get("/students")
def list_students(
    q: str = Query("", max_length=80),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    ids = _student_ids(db, user)
    students = db.scalars(select(User).where(User.id.in_(ids or [-1]), User.role == "student").order_by(User.full_name)).all()
    if q.strip():
        needle = q.strip().lower()
        students = [s for s in students if needle in s.full_name.lower() or needle in s.email.lower()]
    rows = [student_row(db, s, _scope_owner(user)) for s in students]
    order = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda r: (order[r["risk"]["band"]], r["name"].lower()))
    return {"count": len(rows), "students": rows}


@router.get("/students/{student_id}")
def student_detail(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    if student_id not in _student_ids(db, user):
        raise HTTPException(404, "Student not found in your courses")
    student = db.get(User, student_id)
    owner = _scope_owner(user)
    cids = enrolled_course_ids(db, student_id, owner)
    base = student_row(db, student, owner)

    courses = []
    for c in db.scalars(select(Course).where(Course.id.in_(cids or [-1]))):
        m = student_metrics(db, student_id, [c.id])
        courses.append({"id": c.id, "title": c.title, "completion": m["completion"],
                        "lessons_completed": m["lessons_completed"], "lessons_total": m["lessons_total"],
                        "avg_score": m["avg_score"]})

    attempts = db.execute(
        select(Attempt, Quiz, Lesson)
        .join(Quiz, Quiz.id == Attempt.quiz_id)
        .join(Lesson, Lesson.id == Quiz.lesson_id)
        .join(Topic, Topic.id == Lesson.topic_id)
        .where(Attempt.user_id == student_id, Topic.course_id.in_(cids or [-1]))
        .order_by(Attempt.created_at.desc(), Attempt.id.desc())
        .limit(10)
    ).all()
    return {
        **base,
        "course_progress": courses,
        "topic_scores": topic_scores(db, student_id, cids),
        "recent_attempts": [
            {"id": a.id, "lesson": l.title, "quiz": q.title, "score": a.score,
             "created_at": a.created_at.isoformat() if a.created_at else None}
            for a, q, l in attempts
        ],
    }
