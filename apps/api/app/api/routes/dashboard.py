from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/student")
def student_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    enrollments = db.scalars(select(Enrollment).where(Enrollment.user_id == user.id)).all()
    course_ids = [e.course_id for e in enrollments]
    courses = (
        db.scalars(select(Course).where(Course.id.in_(course_ids))).all() if course_ids else []
    )
    attempts = db.scalars(select(Attempt).where(Attempt.user_id == user.id)).all()
    avg = round(sum(a.score for a in attempts) / len(attempts), 2) if attempts else 0.0
    return {
        "courses": [{"id": c.id, "title": c.title, "description": c.description} for c in courses],
        "avg_score": avg,
        "attempt_count": len(attempts),
    }


@router.get("/teacher")
def teacher_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    student_count = db.scalar(select(func.count()).select_from(User).where(User.role == "student"))
    avg_score = db.scalar(select(func.avg(Attempt.score)))
    at_risk = db.scalar(select(func.count()).select_from(Attempt).where(Attempt.score < 50))
    return {
        "student_count": student_count or 0,
        "avg_score": round(float(avg_score), 2) if avg_score else 0.0,
        "at_risk": at_risk or 0,
    }
