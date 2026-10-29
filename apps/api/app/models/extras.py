"""v4 tables. All NEW tables (existing ones untouched) so `create_all` upgrades a live DB safely."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Notification(Base):
    """In-app notification (PDF FR-22)."""

    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40), default="info")
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(String(300), default="")
    link: Mapped[str] = mapped_column(String(200), default="")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CourseJoinCode(Base):
    """Class code a teacher shares so students can join (PDF FR-06)."""

    __tablename__ = "course_join_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)


class LessonResource(Base):
    """Extra learning material attached to a lesson: external link (PDF FR-05)."""

    __tablename__ = "lesson_resources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    url: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordReset(Base):
    """Single-use reset token. Only the SHA-256 hash is stored, never the token itself."""

    __tablename__ = "password_resets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class LiveSession(Base):
    """A scheduled live class (video call link + time). Teachers create, enrolled students join."""

    __tablename__ = "live_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    link: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
