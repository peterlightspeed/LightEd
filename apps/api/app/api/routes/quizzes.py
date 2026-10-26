"""Quiz delivery and grading.

Answers are never sent to the client before submission — the public quiz
payload strips `answer_index`. Grading happens server-side.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
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


@router.post("/quizzes", response_model=QuizOut, status_code=201)
def create_quiz(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("teacher", "admin")),
):
    """Teacher-side quiz creation placeholder.

    TODO: delegate to `ai/lighted_ai/quiz_generator.py` for auto-generation.
    """
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    quiz = Quiz(
        lesson_id=lesson.id,
        title=f"{lesson.title} — checkpoint",
        questions=[
            {
                "prompt": f"Which statement best summarises {lesson.title}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer_index": 0,
                "explanation": "Placeholder question — connect the AI generator next.",
            }
        ],
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return QuizOut(id=quiz.id, lesson_id=lesson.id, title=quiz.title, questions=[])
