"""Revision planner (PDF FR-17): day-by-day plan from weak topics, exam date and daily time."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User
from app.services.analytics import build_plan

router = APIRouter(prefix="/planner", tags=["planner"])


class PlanRequest(BaseModel):
    course_id: int
    exam_date: date
    minutes_per_day: int = Field(default=45, ge=10, le=480)


@router.post("")
def make_plan(payload: PlanRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    course = db.get(Course, payload.course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    try:
        return build_plan(db, user.id, course, payload.exam_date, payload.minutes_per_day)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
