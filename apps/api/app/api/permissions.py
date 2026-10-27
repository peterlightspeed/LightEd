"""Ownership checks for authoring: teachers edit only their own courses; admins edit anything."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.topic import Topic
from app.models.user import User


def course_for_edit(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and course.owner_id != user.id:
        raise HTTPException(403, "You can only edit your own courses")
    return course


def lesson_for_edit(db: Session, lesson_id: int, user: User) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    topic = db.get(Topic, lesson.topic_id)
    course_for_edit(db, topic.course_id, user)
    return lesson
