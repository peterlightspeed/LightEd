from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(String(60), default="General")
    level: Mapped[str] = mapped_column(String(40), default="Beginner")
    # Used by the UI for the coloured course card accent.
    accent: Mapped[str] = mapped_column(String(20), default="blue")
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="courses")  # noqa: F821
    topics: Mapped[list["Topic"]] = relationship(  # noqa: F821
        back_populates="course", cascade="all, delete-orphan", order_by="Topic.order_index"
    )
