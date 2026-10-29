"""LightEd AI/ML module."""

from lighted_ai.gemini_client import GeminiClient
from lighted_ai.provider_router import GrokClient, GroqClient, ProviderRouter
from lighted_ai.revision_planner import build_revision_plan
from lighted_ai.tutor import answer_question
from lighted_ai.weak_topics import detect_weak_topics

__all__ = [
    "GeminiClient",
    "GrokClient",
    "GroqClient",
    "ProviderRouter",
    "answer_question",
    "detect_weak_topics",
    "build_revision_plan",
]
__version__ = "0.1.0"
