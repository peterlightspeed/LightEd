from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])


class TutorRequest(BaseModel):
    question: str
    course_id: int | None = None


class TutorResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.post("/tutor", response_model=TutorResponse)
def tutor(payload: TutorRequest, user: User = Depends(get_current_user)):
    """AI tutor endpoint.

    Sprint 1: returns a stub.
    Sprint 2: wire to the `ai` package:
        from lighted_ai.tutor import answer_question
        result = answer_question(payload.question, course_id=payload.course_id)
    """
    return TutorResponse(
        answer=(
            f"(stub) You asked: '{payload.question}'. "
            "The AI tutor will be connected to the `ai` module in Sprint 2."
        ),
        sources=[],
    )
