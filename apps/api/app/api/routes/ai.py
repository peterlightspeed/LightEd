"""AI tutor: answers ONLY from the student's course material (grounded, with sources).

Uses Gemini when GEMINI_API_KEY is set; otherwise an offline retrieval fallback that quotes
the most relevant lesson passages. Either way the reply cites its sources (PDF FR-09).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.ratelimit import RateLimiter
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.topic import Topic
from app.models.user import User
from app.services import aigen

router = APIRouter(prefix="/ai", tags=["ai"])


class TutorRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    lesson_id: int | None = None
    course_id: int | None = None


class TutorResponse(BaseModel):
    answer: str
    sources: list[str] = []
    provider: str = "offline"


@router.post("/tutor", response_model=TutorResponse, dependencies=[Depends(RateLimiter(30, 60, "tutor"))])
def tutor(payload: TutorRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Which courses may this user ask about? Their enrolments (teachers: their own courses).
    if payload.course_id:
        course_ids = [payload.course_id]
    elif user.role == "student":
        course_ids = list(db.scalars(select(Enrollment.course_id).where(Enrollment.user_id == user.id)))
    else:
        course_ids = list(db.scalars(select(Course.id).where(Course.owner_id == user.id)))

    rows = db.execute(
        select(Lesson, Topic, Course)
        .join(Topic, Topic.id == Lesson.topic_id)
        .join(Course, Course.id == Topic.course_id)
        .where(Course.id.in_(course_ids or [-1]))
    ).all()
    lessons = [{"id": l.id, "title": l.title, "content": l.content or l.summary or "", "course": c.title} for l, t, c in rows]
    answer, sources, provider = aigen.tutor_answer(payload.question.strip(), lessons)
    return TutorResponse(answer=answer, sources=sources, provider=provider)
