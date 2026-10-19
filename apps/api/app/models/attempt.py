from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")  # noqa: F821
