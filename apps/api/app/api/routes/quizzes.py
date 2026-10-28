"""Quiz delivery and grading.

Answers are never sent to the client before submission — the public quiz
payload strips `answer_index`. Grading happens server-side.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.permissions import lesson_for_edit
from app.services import aigen
from app.services.audit import record
from app.services.notify import notify
from pydantic import BaseModel, Field
from fastapi import Request
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.topic import Topic
from app.models.user import User
from app.schemas.learning import (
    AttemptCreate,
    AttemptOut,
    AttemptResult,
    QuestionResult,
    QuizOut,
    QuizQuestionPublic,
)
from app.services.learning import quiz_for_lesson

router = APIRouter(tags=["quizzes"])


@router.get("/lessons/{lesson_id}/quiz", response_model=QuizOut)
def get_lesson_quiz(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quiz = quiz_for_lesson(db, lesson_id)
    if not quiz:
        raise HTTPException(404, "No quiz for this lesson")
    return QuizOut(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        questions=[
            QuizQuestionPublic(prompt=q["prompt"], options=q["options"])
            for q in quiz.questions
        ],
    )


@router.get("/quizzes/{quiz_id}", response_model=QuizOut)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    return QuizOut(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        questions=[
            QuizQuestionPublic(prompt=q["prompt"], options=q["options"])
            for q in quiz.questions
        ],
    )


@router.post("/quizzes/{quiz_id}/attempts", response_model=AttemptResult, status_code=201)
def submit_attempt(
    quiz_id: int,
    payload: AttemptCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions = quiz.questions or []
    results: list[QuestionResult] = []
    correct = 0
    for i, q in enumerate(questions):
        selected = payload.answers[i] if i < len(payload.answers) else None
        is_correct = selected == q.get("answer_index")
        correct += int(is_correct)
        results.append(
            QuestionResult(
                prompt=q["prompt"],
                selected=selected,
                correct_index=q["answer_index"],
                is_correct=is_correct,
                explanation=q.get("explanation", ""),
            )
        )

    total = len(questions)
    score = round((correct / total) * 100, 1) if total else 0.0
    attempt = Attempt(
        quiz_id=quiz.id, user_id=user.id, score=score, answers=payload.answers
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    _alert_low_score(db, quiz, user, score)

    return AttemptResult(
        id=attempt.id,
        quiz_id=quiz.id,
        score=score,
        correct_count=correct,
        total=total,
        results=results,
        created_at=attempt.created_at,
    )


@router.get("/attempts/me", response_model=list[AttemptOut])
def my_attempts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(Attempt, Quiz, Lesson, Topic)
        .join(Quiz, Attempt.quiz_id == Quiz.id)
        .join(Lesson, Quiz.lesson_id == Lesson.id)
        .join(Topic, Lesson.topic_id == Topic.id)
        .where(Attempt.user_id == user.id)
        .order_by(Attempt.created_at.desc())
    ).all()
    return [
        AttemptOut(
            id=a.id,
            quiz_id=a.quiz_id,
            quiz_title=q.title,
            lesson_title=l.title,
            course_title=t.title,
            score=a.score,
            created_at=a.created_at,
        )
        for a, q, l, t in rows
    ]




# ---------------------------------------------------------------- Teacher authoring
class GenerateRequest(BaseModel):
    num_questions: int = Field(default=5, ge=1, le=10)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class QuizSave(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    questions: list[dict]


@router.post("/lessons/{lesson_id}/quiz/generate")
def generate_quiz_draft(
    lesson_id: int,
    payload: GenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    """Draft questions from the lesson text. NOT saved: the teacher reviews/edits, then PUTs."""
    lesson = lesson_for_edit(db, lesson_id, user)
    pool = [w for t in db.scalars(select(Lesson.title).limit(40)) for w in t.lower().split() if len(w) > 4]
    questions, provider = aigen.generate_questions(
        lesson.title, lesson.content or lesson.summary or "", payload.num_questions, payload.difficulty, pool
    )
    return {"provider": provider, "questions": questions}


@router.get("/lessons/{lesson_id}/quiz/edit")
def get_quiz_for_edit(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    """Quiz WITH answers, for the owning teacher/admin only."""
    lesson_for_edit(db, lesson_id, user)
    quiz = quiz_for_lesson(db, lesson_id)
    return {"title": quiz.title if quiz else "", "questions": quiz.questions if quiz else []}


@router.put("/lessons/{lesson_id}/quiz")
def save_quiz(
    lesson_id: int,
    payload: QuizSave,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    """Approve + publish: create or replace the lesson's quiz after teacher review."""
    lesson = lesson_for_edit(db, lesson_id, user)
    try:
        questions = aigen.validate_questions(payload.questions)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    quiz = quiz_for_lesson(db, lesson_id)
    title = (payload.title or f"{lesson.title} — checkpoint").strip()
    if quiz:
        quiz.title, quiz.questions = title, questions
    else:
        quiz = Quiz(lesson_id=lesson_id, title=title, questions=questions)
        db.add(quiz)
    db.commit()
    db.refresh(quiz)
    _notify_students(db, lesson, quiz)
    record(db, "quiz.publish", user=user, detail=f"lesson {lesson_id}: {len(questions)} questions", request=request)
    return {"id": quiz.id, "lesson_id": lesson_id, "title": quiz.title, "question_count": len(questions)}


def _notify_students(db: Session, lesson: Lesson, quiz: Quiz) -> None:
    """Tell every enrolled student that a new quiz is available (PDF FR-22)."""
    from app.models.enrollment import Enrollment
    from app.models.topic import Topic

    topic = db.get(Topic, lesson.topic_id)
    for uid in db.scalars(select(Enrollment.user_id).where(Enrollment.course_id == topic.course_id)):
        notify(db, uid, "New quiz available", f"{lesson.title} — checkpoint is ready.", kind="quiz", link=f"/quizzes/{quiz.id}")


def _alert_low_score(db: Session, quiz: Quiz, student: User, score: float) -> None:
    """Teacher alert when a student scores under 50% (an early at-risk signal)."""
    if score >= 50:
        return
    from app.models.course import Course
    from app.models.topic import Topic

    lesson = db.get(Lesson, quiz.lesson_id)
    course = db.get(Course, db.get(Topic, lesson.topic_id).course_id)
    notify(db, course.owner_id, "Student may need help", f"{student.full_name} scored {round(score)}% on {lesson.title}.",
           kind="risk", link=f"/students/{student.id}")
