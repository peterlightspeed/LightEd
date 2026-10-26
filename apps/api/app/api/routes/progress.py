"""Student progress + analytics endpoint."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.topic import Topic
from app.models.user import User
from app.schemas.learning import CourseProgressOut, LessonProgressOut, ProgressOut
from app.services.learning import average_score

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/me", response_model=ProgressOut)
def my_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    enrolled_ids = list(
        db.scalars(select(Enrollment.course_id).where(Enrollment.user_id == user.id)).all()
    )
    courses = (
        db.scalars(
            select(Course)
            .options(selectinload(Course.topics).selectinload(Topic.lessons))
            .where(Course.id.in_(enrolled_ids))
        ).all()
        if enrolled_ids
        else []
    )

    # All completed lesson ids (used for the percentage maths).
    completed_rows = db.execute(
        select(Progress.lesson_id, Progress.completed_at)
        .where(Progress.user_id == user.id, Progress.completed.is_(True))
    ).all()
    completed_ids = {r[0] for r in completed_rows}

    # Most recent completions (used for the activity list).
    recent_rows = db.execute(
        select(Progress, Lesson, Course)
        .join(Lesson, Progress.lesson_id == Lesson.id)
        .join(Topic, Lesson.topic_id == Topic.id)
        .join(Course, Topic.course_id == Course.id)
        .where(Progress.user_id == user.id, Progress.completed.is_(True))
        .order_by(Progress.completed_at.desc())
        .limit(8)
    ).all()

    course_progress: list[CourseProgressOut] = []
    total = 0
    done = 0
    for c in courses:
        ids = [l.id for t in c.topics for l in t.lessons]
        c_done = len([i for i in ids if i in completed_ids])
        total += len(ids)
        done += c_done
        course_progress.append(
            CourseProgressOut(
                course_id=c.id,
                title=c.title,
                progress=round((c_done / len(ids)) * 100) if ids else 0,
                lessons_completed=c_done,
                lessons_total=len(ids),
            )
        )

    # Streak: consecutive days (ending today) with at least one completion.
    dates = {r[1].date() for r in completed_rows if r[1]}
    streak = 0
    cursor = datetime.now(timezone.utc).date()
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)

    return ProgressOut(
        lessons_completed=done,
        lessons_total=total,
        overall_progress=round((done / total) * 100) if total else 0,
        avg_score=average_score(db, user.id),
        streak_days=streak,
        courses=course_progress,
        recent_lessons=[
            LessonProgressOut(
                lesson_id=lesson.id,
                title=lesson.title,
                course_title=course.title,
                completed=True,
                completed_at=prog.completed_at,
            )
            for prog, lesson, course in recent_rows
        ],
    )
