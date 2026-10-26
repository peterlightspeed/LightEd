from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    title: Mapped[str] = mapped_column(String(200), default="Lesson quiz")
    # [{ "prompt": str, "options": [str], "answer_index": int, "explanation": str }]
    questions: Mapped[list] = mapped_column(JSON, default=list)

    lesson: Mapped["Lesson"] = relationship(back_populates="quizzes")  # noqa: F821
    attempts: Mapped[list["Attempt"]] = relationship(  # noqa: F821
        back_populates="quiz", cascade="all, delete-orphan"
    )
