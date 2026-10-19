from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.learning import AttemptCreate, AttemptOut, QuizCreate, QuizOut

router = APIRouter(tags=["quizzes"])


def _generate_questions(lesson: Lesson, num: int) -> list[dict]:
    """Placeholder quiz generator.

    In Sprint 2 this delegates to the `ai` package:
        from lighted_ai.quiz_generator import generate_quiz
        return generate_quiz(lesson.content, num)
    """
    return [
        {
            "prompt": f"Sample question {i + 1} about '{lesson.title}'?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer_index": 0,
        }
        for i in range(num)
    ]


@router.post("/quizzes", response_model=QuizOut, status_code=201)
def create_quiz(
    payload: QuizCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    lesson = db.get(Lesson, payload.lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    quiz = Quiz(lesson_id=lesson.id, questions=_generate_questions(lesson, payload.num_questions))
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@router.get("/quizzes/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    return quiz


@router.post("/attempts", response_model=AttemptOut, status_code=201)
def submit_attempt(
    payload: AttemptCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quiz = db.get(Quiz, payload.quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions = quiz.questions or []
    correct = sum(
        1
        for i, q in enumerate(questions)
        if i < len(payload.answers) and payload.answers[i] == q.get("answer_index")
    )
    score = round((correct / len(questions)) * 100, 2) if questions else 0.0

    attempt = Attempt(quiz_id=quiz.id, user_id=user.id, score=score, answers=payload.answers)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/attempts/me", response_model=list[AttemptOut])
def my_attempts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Attempt).where(Attempt.user_id == user.id)).all()
