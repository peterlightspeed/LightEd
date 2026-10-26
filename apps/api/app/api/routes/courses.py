"""Course catalogue, curriculum, enrolment and authoring routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_optional_user, require_roles
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.topic import Topic
from app.models.user import User
from app.schemas.learning import (
    CourseCreate,
    CourseDetail,
    CourseOut,
    EnrollmentOut,
    LessonCreate,
    LessonSummary,
    TopicCreate,
    TopicOut,
)
from app.services.learning import (
    completed_lesson_ids,
    course_to_detail,
    course_to_out,
    is_enrolled,
    load_course,
)

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=list[CourseOut])
def list_courses(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Public catalogue. Progress/enrolment are filled in when authenticated."""
    courses = db.scalars(
        select(Course)
        .options(
            selectinload(Course.owner),
            selectinload(Course.topics).selectinload(Topic.lessons),
        )
        .where(Course.published.is_(True))
        .order_by(Course.id)
    ).all()
    completed = completed_lesson_ids(db, user.id) if user else set()
    enrolled_ids = set()
    if user:
        enrolled_ids = set(
            db.scalars(select(Enrollment.course_id).where(Enrollment.user_id == user.id)).all()
        )
    return [
        course_to_out(c, completed=completed, enrolled=c.id in enrolled_ids) for c in courses
    ]


@router.get("/courses/mine", response_model=list[CourseOut])
def my_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Courses the current student is enrolled in (or a teacher owns)."""
    if user.role == "teacher":
        courses = db.scalars(
            select(Course)
            .options(
                selectinload(Course.owner),
                selectinload(Course.topics).selectinload(Topic.lessons),
            )
            .where(Course.owner_id == user.id)
        ).all()
        return [course_to_out(c, completed=set(), enrolled=False) for c in courses]

    course_ids = db.scalars(
        select(Enrollment.course_id).where(Enrollment.user_id == user.id)
    ).all()
    if not course_ids:
        return []
    courses = db.scalars(
        select(Course)
        .options(
            selectinload(Course.owner),
            selectinload(Course.topics).selectinload(Topic.lessons),
        )
        .where(Course.id.in_(course_ids))
    ).all()
    completed = completed_lesson_ids(db, user.id)
    return [course_to_out(c, completed=completed, enrolled=True) for c in courses]


@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    course = Course(**payload.model_dump(), owner_id=user.id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course_to_out(course, completed=set(), enrolled=False)


@router.get("/courses/{course_id}", response_model=CourseDetail)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    course = load_course(db, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    completed = completed_lesson_ids(db, user.id) if user else set()
    return course_to_detail(
        course, completed=completed, enrolled=is_enrolled(db, user.id if user else None, course_id)
    )


@router.post("/courses/{course_id}/enroll", response_model=EnrollmentOut, status_code=201)
def enroll(
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.get(Course, course_id):
        raise HTTPException(404, "Course not found")
    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.user_id == user.id, Enrollment.course_id == course_id
        )
    )
    if existing:
        return existing
    enrollment = Enrollment(user_id=user.id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


# ---------------------------------------------------------------- Authoring
@router.post("/courses/{course_id}/topics", response_model=TopicOut, status_code=201)
def create_topic(
    course_id: int,
    payload: TopicCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    if not db.get(Course, course_id):
        raise HTTPException(404, "Course not found")
    topic = Topic(course_id=course_id, title=payload.title, order_index=payload.order_index)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicOut(id=topic.id, title=topic.title, order_index=topic.order_index, lessons=[])


@router.post("/lessons", response_model=LessonSummary, status_code=201)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    if not db.get(Topic, payload.topic_id):
        raise HTTPException(404, "Topic not found")
    lesson = Lesson(**payload.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return LessonSummary(
        id=lesson.id,
        title=lesson.title,
        summary=lesson.summary,
        duration_minutes=lesson.duration_minutes,
        order_index=lesson.order_index,
    )


@router.get("/enrollments/me", response_model=list[EnrollmentOut])
def my_enrollments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Enrollment).where(Enrollment.user_id == user.id)).all()
