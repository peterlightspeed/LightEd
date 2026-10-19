from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.topic import Topic
from app.models.user import User
from app.schemas.learning import (
    CourseCreate,
    CourseOut,
    EnrollmentCreate,
    EnrollmentOut,
    LessonCreate,
    LessonOut,
    TopicCreate,
    TopicOut,
)

router = APIRouter(tags=["courses"])


# ---------- Courses ----------
@router.get("/courses", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.scalars(select(Course)).all()


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
    return course


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return course


# ---------- Topics ----------
@router.get("/courses/{course_id}/topics", response_model=list[TopicOut])
def list_topics(course_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(Topic).where(Topic.course_id == course_id)).all()


@router.post("/topics", response_model=TopicOut, status_code=201)
def create_topic(
    payload: TopicCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    topic = Topic(**payload.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


# ---------- Lessons ----------
@router.get("/topics/{topic_id}/lessons", response_model=list[LessonOut])
def list_lessons(topic_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(Lesson).where(Lesson.topic_id == topic_id)).all()


@router.post("/lessons", response_model=LessonOut, status_code=201)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    lesson = Lesson(**payload.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


# ---------- Enrollments ----------
@router.post("/enrollments", response_model=EnrollmentOut, status_code=201)
def enroll(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    enrollment = Enrollment(user_id=user.id, course_id=payload.course_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/enrollments/me", response_model=list[EnrollmentOut])
def my_enrollments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Enrollment).where(Enrollment.user_id == user.id)).all()
