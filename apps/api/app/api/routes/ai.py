"""AI tutor: answers ONLY from the student's course material (grounded, with sources).

Uses Gemini when GEMINI_API_KEY is set; otherwise an offline retrieval fallback that quotes
the most relevant lesson passages. Either way the reply cites its sources (PDF FR-09).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.ratelimit import RateLimiter
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.topic import Topic
from app.models.user import User
from app.services import aigen

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|tutor)$")
    text: str = Field(max_length=2000)


class TutorRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    lesson_id: int | None = None
    course_id: int | None = None
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)


class TutorResponse(BaseModel):
    answer: str
    sources: list[str] = []
    provider: str = "offline"
    notice: str | None = None  # set when the AI model could not be used (shown to the student)
    suggestions: list[dict] = []  # courses worth looking at: [{id, title, subject, level}]
    actions: list[dict] = []  # next-step buttons: [{label, href}]


@router.post("/tutor", response_model=TutorResponse, dependencies=[Depends(RateLimiter(30, 60, "tutor"))])
def tutor(payload: TutorRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Which courses may this user ask about? Their enrolments (teachers: their own courses).
    if payload.course_id:
        course_ids = [payload.course_id]
    elif user.role == "student":
        course_ids = list(db.scalars(select(Enrollment.course_id).where(Enrollment.user_id == user.id)))
    else:
        course_ids = list(db.scalars(select(Course.id).where(Course.owner_id == user.id)))

    rows = db.execute(
        select(Lesson, Topic, Course)
        .join(Topic, Topic.id == Lesson.topic_id)
        .join(Course, Course.id == Topic.course_id)
        .where(Course.id.in_(course_ids or [-1]))
    ).all()
    lessons = [{"id": l.id, "title": l.title, "content": l.content or l.summary or "", "course": c.title} for l, t, c in rows]
    history = [t.model_dump() for t in payload.history]
    answer, sources, provider, notice = aigen.tutor_answer(payload.question.strip(), lessons, history)
    if sources:
        return TutorResponse(answer=answer, sources=sources, provider=provider, notice=notice)

    # Nothing in the course material matched: don't dead-end, point the person to a next step.
    if user.role == "student":
        answer, suggestions, actions = _student_guidance(db, user, payload.question, enrolled=bool(course_ids))
        return TutorResponse(answer=answer, provider="guide", suggestions=suggestions, actions=actions)

    help_text = aigen.teacher_assist(payload.question.strip(), history)
    if help_text:
        return TutorResponse(answer=help_text, provider="gemini",
                             actions=[{"label": "Open my courses", "href": "/courses"}])
    return TutorResponse(answer=_teacher_guidance(has_lessons=bool(lessons)), provider="guide",
                         actions=[{"label": "Create a course", "href": "/courses?new=1"}, {"label": "My courses", "href": "/courses"}])


def _student_guidance(db: Session, user: User, question: str, enrolled: bool) -> tuple[str, list[dict], list[dict]]:
    mine = set(db.scalars(select(Enrollment.course_id).where(Enrollment.user_id == user.id)))
    topic = aigen._topic_terms(question)
    scored = []
    for c in db.scalars(select(Course).where(Course.published.is_(True))):
        if c.id in mine:
            continue
        hay = aigen._terms(f"{c.title} {c.subject} {c.description}")
        scored.append((len(topic & hay), c.id, c))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    matched = [c for sc, _, c in scored if sc > 0][:3]
    picks = matched or [c for _, _, c in scored[:3]]
    suggestions = [{"id": c.id, "title": c.title, "subject": c.subject, "level": c.level} for c in picks]

    how = ("To enrol: open **Courses**, tap a course and press **Enrol**. Got a code from your teacher? "
           "Enter it under **Join with a class code** on the Courses page.")
    if not enrolled:
        head = "You're not enrolled in any course yet, so I have no lessons to answer from."
    else:
        head = "I couldn't find that in your enrolled courses. Try a key word from the lesson, or ask your teacher."
    if suggestions:
        tail = ("These courses look relevant to your question:" if matched else "A few courses you could start with:")
    else:
        tail = "No other courses are available yet. Ask your teacher for a class code."
    return f"{head}\n\n{how}\n\n{tail}", suggestions, [
        {"label": "Browse courses", "href": "/courses"}, {"label": "Join with a class code", "href": "/courses"}]


def _teacher_guidance(has_lessons: bool) -> str:
    start = "" if has_lessons else "You haven't added any lessons yet, and I answer from your lesson text, so let's start there.\n\n"
    return (
        start + "Here is how to get your course ready for students:\n\n"
        "1. **Create a course** under Courses, then add topics (I can suggest them).\n"
        "2. **Add lessons** by typing, pasting, or importing text from a PDF. Use **Draft with AI** for a first version.\n"
        "3. **Add videos and links**: YouTube, Instagram, or recorded Zoom/Meet links under Resource links.\n"
        "4. **Publish a quiz** per lesson, then share your **class code** so students can join.\n\n"
        "Free places to find teaching material: OpenStax, Khan Academy, MIT OpenCourseWare, OER Commons, Wikibooks and YouTube educational channels. Always check each licence before reusing it."
    )


class DraftLessonRequest(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    course_title: str = Field(default="", max_length=200)
    level: str = Field(default="Beginner", max_length=40)


@router.post("/draft-lesson", dependencies=[Depends(RateLimiter(10, 60, "ai-draft"))])
def draft_lesson(payload: DraftLessonRequest, user: User = Depends(require_roles("teacher", "admin"))):
    summary, content, provider = aigen.draft_lesson(payload.title.strip(), payload.course_title.strip(), payload.level)
    return {"summary": summary, "content": content, "provider": provider}


class SuggestTopicsRequest(BaseModel):
    course_title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=1000)
    count: int = Field(default=6, ge=3, le=10)


@router.post("/suggest-topics", dependencies=[Depends(RateLimiter(10, 60, "ai-topics"))])
def suggest_topics(payload: SuggestTopicsRequest, user: User = Depends(require_roles("teacher", "admin"))):
    topics, provider = aigen.suggest_topics(payload.course_title.strip(), payload.description, payload.count)
    return {"topics": topics, "provider": provider}


@router.get("/status", dependencies=[Depends(RateLimiter(10, 60, "ai-status"))])
def ai_status(user: User = Depends(get_current_user)):
    """Is the AI actually reachable? Makes one tiny live call and reports the result (never the key)."""
    return aigen.gemini_status()
