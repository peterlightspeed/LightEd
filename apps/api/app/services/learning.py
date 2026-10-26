"""Progress + course assembly helpers.

These functions are shared by the course, lesson, progress and dashboard
routes so the percentage maths lives in exactly one place.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.quiz import Quiz
from app.models.topic import Topic
from app.schemas.learning import CourseDetail, CourseOut, LessonSummary, TopicOut


def completed_lesson_ids(db: Session, user_id: int) -> set[int]:
    rows = db.scalars(
        select(Progress.lesson_id).where(
            Progress.user_id == user_id, Progress.completed.is_(True)
        )
    ).all()
    return set(rows)


def course_lesson_ids(db: Session, course_id: int) -> list[int]:
    return list(
        db.scalars(
            select(Lesson.id)
            .join(Topic, Lesson.topic_id == Topic.id)
            .where(Topic.course_id == course_id)
        ).all()
    )


def quiz_for_lesson(db: Session, lesson_id: int) -> Quiz | None:
    return db.scalar(select(Quiz).where(Quiz.lesson_id == lesson_id))


def course_to_out(
    course: Course,
    *,
    completed: set[int],
    enrolled: bool,
    lesson_ids: list[int] | None = None,
) -> CourseOut:
    ids = lesson_ids if lesson_ids is not None else [
        lesson.id for topic in course.topics for lesson in topic.lessons
    ]
    total = len(ids)
    done = len([i for i in ids if i in completed])
    progress = round((done / total) * 100) if total else 0
    return CourseOut(
        id=course.id,
        title=course.title,
        description=course.description,
        subject=course.subject,
        level=course.level,
        accent=course.accent,
        owner_id=course.owner_id,
        owner_name=course.owner.full_name if course.owner else "",
        lesson_count=total,
        topic_count=len(course.topics),
        enrolled=enrolled,
        progress=progress,
    )


def load_course(db: Session, course_id: int) -> Course | None:
    """Eager-load owner + curriculum so serialisation does not N+1."""
    return db.scalar(
        select(Course)
        .options(
            selectinload(Course.owner),
            selectinload(Course.topics).selectinload(Topic.lessons).selectinload(Lesson.quizzes),
        )
        .where(Course.id == course_id)
    )


def course_to_detail(course: Course, *, completed: set[int], enrolled: bool) -> CourseDetail:
    base = course_to_out(course, completed=completed, enrolled=enrolled)
    topics = []
    for topic in sorted(course.topics, key=lambda t: t.order_index):
        lessons = [
            LessonSummary(
                id=lesson.id,
                title=lesson.title,
                summary=lesson.summary,
                duration_minutes=lesson.duration_minutes,
                order_index=lesson.order_index,
                completed=lesson.id in completed,
                quiz_id=lesson.quizzes[0].id if lesson.quizzes else None,
            )
            for lesson in sorted(topic.lessons, key=lambda l: l.order_index)
        ]
        topics.append(
            TopicOut(
                id=topic.id,
                title=topic.title,
                order_index=topic.order_index,
                lessons=lessons,
            )
        )
    return CourseDetail(**base.model_dump(), topics=topics)


def is_enrolled(db: Session, user_id: int | None, course_id: int) -> bool:
    if not user_id:
        return False
    return (
        db.scalar(
            select(Enrollment.id).where(
                Enrollment.user_id == user_id, Enrollment.course_id == course_id
            )
        )
        is not None
    )


def average_score(db: Session, user_id: int) -> float:
    value = db.scalar(select(func.avg(Attempt.score)).where(Attempt.user_id == user_id))
    return round(float(value), 1) if value is not None else 0.0
