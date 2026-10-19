from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")

    topic: Mapped["Topic"] = relationship(back_populates="lessons")  # noqa: F821
    quizzes: Mapped[list["Quiz"]] = relationship(  # noqa: F821
        back_populates="lesson", cascade="all, delete-orphan"
    )
