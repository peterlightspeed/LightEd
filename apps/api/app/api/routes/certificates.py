"""Course completion certificates.

A student earns one by completing every lesson in a course. The certificate id embeds the user and
course ids plus a short HMAC, so anyone (an employer, a parent) can verify it at /certificates/verify/{id}
without logging in, and nobody can forge a valid id without the server secret.
"""
import hashlib
import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.topic import Topic
from app.models.user import User
from app.services.analytics import student_metrics

router = APIRouter(tags=["certificates"])


def _sig(user_id: int, course_id: int) -> str:
    return hmac.new(settings.jwt_secret_key.encode(), f"cert:{user_id}:{course_id}".encode(), hashlib.sha256).hexdigest()[:8].upper()


def make_cert_id(user_id: int, course_id: int) -> str:
    return f"LE-{user_id}-{course_id}-{_sig(user_id, course_id)}"


def _completion_date(db: Session, user_id: int, course_id: int) -> datetime | None:
    lesson_ids = select(Lesson.id).join(Topic, Topic.id == Lesson.topic_id).where(Topic.course_id == course_id)
    rows = db.scalars(select(Progress.completed_at).where(Progress.user_id == user_id, Progress.completed.is_(True), Progress.lesson_id.in_(lesson_ids)))
    stamps = [r for r in rows if r]
    return max(stamps) if stamps else None


def _payload(db: Session, student: User, course: Course) -> dict:
    m = student_metrics(db, student.id, [course.id])
    done = _completion_date(db, student.id, course.id) or datetime.now(timezone.utc)
    owner = db.get(User, course.owner_id)
    return {
        "certificate_id": make_cert_id(student.id, course.id),
        "student_name": student.full_name,
        "course_id": course.id,
        "course_title": course.title,
        "teacher_name": owner.full_name if owner else "LightEd",
        "completed_on": done.date().isoformat(),
        "avg_score": m["avg_score"],
        "lessons_completed": m["lessons_completed"],
    }


def _is_complete(db: Session, user_id: int, course_id: int) -> tuple[bool, dict]:
    m = student_metrics(db, user_id, [course_id])
    return (m["lessons_total"] > 0 and m["completion"] >= 100), m


@router.get("/courses/{course_id}/certificate")
def my_certificate(course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    enrolled = db.scalar(select(Enrollment.id).where(Enrollment.user_id == user.id, Enrollment.course_id == course_id))
    if not enrolled:
        raise HTTPException(403, "Enrol in this course to earn its certificate.")
    ok, m = _is_complete(db, user.id, course_id)
    if not ok:
        left = max(m["lessons_total"] - m["lessons_completed"], 0)
        raise HTTPException(403, f"Finish all lessons to unlock your certificate ({left} left).")
    return _payload(db, user, course)


@router.get("/certificates/verify/{cert_id}")
def verify_certificate(cert_id: str, db: Session = Depends(get_db)):
    """Public: confirms a certificate id is genuine. Returns only the name, course and date."""
    try:
        _, uid, cid, sig = cert_id.strip().upper().split("-")
        uid, cid = int(uid), int(cid)
    except ValueError:
        return {"valid": False}
    student, course = db.get(User, uid), db.get(Course, cid)
    if not student or not course or not hmac.compare_digest(sig, _sig(uid, cid)):
        return {"valid": False}
    ok, _ = _is_complete(db, uid, cid)
    if not ok:
        return {"valid": False}
    p = _payload(db, student, course)
    return {"valid": True, "student_name": p["student_name"], "course_title": p["course_title"], "completed_on": p["completed_on"]}
