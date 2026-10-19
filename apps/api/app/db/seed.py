"""Seed demo data: run with `python -m app.db.seed`.

Creates one teacher, two students, a sample course with topics and lessons,
and a couple of quiz attempts so dashboards have data.
"""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.attempt import Attempt
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.topic import Topic
from app.models.user import User


def seed() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == "teacher@lighted.dev")):
            print("Seed data already present. Skipping.")
            return

        teacher = User(
            full_name="Tara Teacher",
            email="teacher@lighted.dev",
            hashed_password=hash_password("password123"),
            role="teacher",
        )
        student = User(
            full_name="Sam Student",
            email="student@lighted.dev",
            hashed_password=hash_password("password123"),
            role="student",
        )
        db.add_all([teacher, student])
        db.flush()

        course = Course(
            title="Intro to Calculus",
            description="Limits, derivatives, and integrals — the foundations.",
            owner_id=teacher.id,
        )
        db.add(course)
        db.flush()

        topic = Topic(course_id=course.id, title="Derivatives", order_index=1)
        db.add(topic)
        db.flush()

        lesson = Lesson(
            topic_id=topic.id,
            title="What is a derivative?",
            content=(
                "A derivative measures how a function changes as its input changes. "
                "It is the slope of the tangent line at a point."
            ),
        )
        db.add(lesson)
        db.flush()

        quiz = Quiz(
            lesson_id=lesson.id,
            questions=[
                {
                    "prompt": "What does a derivative measure?",
                    "options": ["Area", "Rate of change", "Volume", "Length"],
                    "answer_index": 1,
                }
            ],
        )
        db.add(quiz)
        db.flush()

        db.add(Enrollment(user_id=student.id, course_id=course.id))
        db.add(Attempt(quiz_id=quiz.id, user_id=student.id, score=75.0, answers=[1]))

        db.commit()
        print("Seed complete.")
        print("  teacher@lighted.dev / password123")
        print("  student@lighted.dev / password123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
