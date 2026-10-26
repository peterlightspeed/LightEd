"""Schemas for courses, lessons, quizzes, attempts and progress.

Kept in one module because they are small and tightly related. Split later if
the surface grows.
"""
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- Courses
class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = ""
    subject: str = "General"
    level: str = "Beginner"
    accent: str = "blue"


class TopicCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    order_index: int = 1


class LessonCreate(BaseModel):
    topic_id: int
    title: str = Field(min_length=2, max_length=200)
    content: str = ""
    summary: str = ""
    duration_minutes: int = 10
    order_index: int = 1


class LessonSummary(BaseModel):
    id: int
    title: str
    summary: str = ""
    duration_minutes: int = 10
    order_index: int = 1
    completed: bool = False
    quiz_id: int | None = None


class TopicOut(BaseModel):
    id: int
    title: str
    order_index: int
    lessons: list[LessonSummary] = []


class CourseOut(BaseModel):
    id: int
    title: str
    description: str
    subject: str
    level: str
    accent: str
    owner_id: int
    owner_name: str = ""
    lesson_count: int = 0
    topic_count: int = 0
    enrolled: bool = False
    progress: int = 0  # 0-100


class CourseDetail(CourseOut):
    topics: list[TopicOut] = []


# ---------------------------------------------------------------- Lessons
class LessonDetail(BaseModel):
    id: int
    title: str
    content: str
    summary: str
    duration_minutes: int
    order_index: int
    topic_id: int
    topic_title: str
    course_id: int
    course_title: str
    quiz_id: int | None = None
    completed: bool = False
    next_lesson_id: int | None = None
    prev_lesson_id: int | None = None


# ---------------------------------------------------------------- Quizzes
class QuizQuestionPublic(BaseModel):
    """Question shape sent to the client — deliberately omits the answer."""

    prompt: str
    options: list[str]


class QuizOut(BaseModel):
    id: int
    lesson_id: int
    title: str
    questions: list[QuizQuestionPublic]


class AttemptCreate(BaseModel):
    answers: list[int]


class QuestionResult(BaseModel):
    prompt: str
    selected: int | None
    correct_index: int
    is_correct: bool
    explanation: str = ""


class AttemptResult(BaseModel):
    id: int
    quiz_id: int
    score: float
    correct_count: int
    total: int
    results: list[QuestionResult]
    created_at: datetime


class AttemptOut(BaseModel):
    id: int
    quiz_id: int
    quiz_title: str = ""
    lesson_title: str = ""
    course_title: str = ""
    score: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------- Progress
class LessonProgressOut(BaseModel):
    lesson_id: int
    title: str
    course_title: str
    completed: bool
    completed_at: datetime | None = None


class CourseProgressOut(BaseModel):
    course_id: int
    title: str
    progress: int
    lessons_completed: int
    lessons_total: int


class ProgressOut(BaseModel):
    lessons_completed: int
    lessons_total: int
    overall_progress: int
    avg_score: float
    streak_days: int
    courses: list[CourseProgressOut]
    recent_lessons: list[LessonProgressOut]


class EnrollmentOut(BaseModel):
    id: int
    user_id: int
    course_id: int
    status: str

    model_config = {"from_attributes": True}
