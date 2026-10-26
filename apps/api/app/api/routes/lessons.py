"""Lesson reading + completion routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.quiz import Quiz
from app.models.topic import Topic
from app.models.user import User
from app.schemas.learning import LessonDetail
from app.services.learning import completed_lesson_ids

router = APIRouter(prefix="/lessons", tags=["lessons"])


def _ordered_lessons(db: Session, course_id: int) -> list[Lesson]:
    """All lessons of a course in curriculum order (used for prev/next)."""
    return list(
        db.scalars(
            select(Lesson)
            .join(Topic, Lesson.topic_id == Topic.id)
            .where(Topic.course_id == course_id)
            .order_by(Topic.order_index, Lesson.order_index)
        ).all()
    )


@router.get("/{lesson_id}", response_model=LessonDetail)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lesson = db.scalar(
        select(Lesson)
        .options(selectinload(Lesson.topic).selectinload(Topic.course), selectinload(Lesson.quizzes))
        .where(Lesson.id == lesson_id)
    )
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    course = lesson.topic.course
    siblings = _ordered_lessons(db, course.id)
    idx = next((i for i, l in enumerate(siblings) if l.id == lesson.id), -1)
    completed = completed_lesson_ids(db, user.id)
    quiz = lesson.quizzes[0] if lesson.quizzes else None

    return LessonDetail(
        id=lesson.id,
        title=lesson.title,
        content=lesson.content,
        summary=lesson.summary,
        duration_minutes=lesson.duration_minutes,
        order_index=lesson.order_index,
        topic_id=lesson.topic_id,
        topic_title=lesson.topic.title,
        course_id=course.id,
        course_title=course.title,
        quiz_id=quiz.id if quiz else None,
        completed=lesson.id in completed,
        next_lesson_id=siblings[idx + 1].id if 0 <= idx < len(siblings) - 1 else None,
        prev_lesson_id=siblings[idx - 1].id if idx > 0 else None,
    )


@router.post("/{lesson_id}/complete", response_model=LessonDetail)
def complete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Idempotently mark a lesson complete, then return the updated lesson."""
    if not db.get(Lesson, lesson_id):
        raise HTTPException(404, "Lesson not found")

    row = db.scalar(
        select(Progress).where(Progress.user_id == user.id, Progress.lesson_id == lesson_id)
    )
    if row:
        row.completed = True
    else:
        db.add(Progress(user_id=user.id, lesson_id=lesson_id, completed=True))
    db.commit()

    return get_lesson(lesson_id, db=db, user=user)
