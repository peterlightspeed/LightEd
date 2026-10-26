"""Import all models so Alembic can discover them via Base.metadata."""

from app.db.session import Base  # noqa: F401
from app.models.attempt import Attempt  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.enrollment import Enrollment  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.progress import Progress  # noqa: F401
from app.models.quiz import Quiz  # noqa: F401
from app.models.topic import Topic  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Course",
    "Topic",
    "Lesson",
    "Enrollment",
    "Quiz",
    "Attempt",
    "Progress",
]
