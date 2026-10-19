from sqlalchemy import ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    # questions stored as JSON: [{prompt, options:[...], answer_index}]
    questions: Mapped[list] = mapped_column(JSON, default=list)

    lesson: Mapped["Lesson"] = relationship(back_populates="quizzes")  # noqa: F821
    attempts: Mapped[list["Attempt"]] = relationship(  # noqa: F821
        back_populates="quiz", cascade="all, delete-orphan"
    )
