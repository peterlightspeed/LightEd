"""AI tutor bridge.

The MVP returns a helpful canned answer so the UI is fully clickable. The real
model lives in the separate `ai/` package and can be enabled without touching
the frontend.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])


class TutorRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    lesson_id: int | None = None
    course_id: int | None = None


class TutorResponse(BaseModel):
    answer: str
    sources: list[str] = []
    provider: str = "stub"


@router.post("/tutor", response_model=TutorResponse)
def tutor(payload: TutorRequest, user: User = Depends(get_current_user)):
    """Answer a student question.

    Swap the body for:
        from lighted_ai.tutor import answer_question
        result = answer_question(payload.question, course_id=payload.course_id)
    once GEMINI_API_KEY is configured.
    """
    q = payload.question.strip()
    return TutorResponse(
        answer=(
            f"Great question about “{q}”. Here is a simple way to think about it: "
            "break the idea into its smallest parts, connect it to something you "
            "already know, then test yourself with one example. "
            "The full AI tutor will be connected in the next sprint — for now this "
            "is a guided placeholder so you can try the flow end to end."
        ),
        sources=[],
        provider="stub",
    )
