import os
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_project_env() -> dict[str, str]:
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = raw_line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    for key, value in values.items():
        os.environ.setdefault(key, value)
        if key == "GEMINI_API_KEY" and "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = value
        if key == "GOOGLE_API_KEY" and "GEMINI_API_KEY" not in os.environ:
            os.environ["GEMINI_API_KEY"] = value
    return values


_load_project_env()


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "LIGHTED_GEMINI_API_KEY",
        ),
    )
    gemini_model: str = Field(
        default="gemini-3.8-flash",
        validation_alias=AliasChoices("GEMINI_MODEL", "LIGHTED_GEMINI_MODEL"),
    )
    groq_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GROQ_API_KEY",
            "GROK_API_KEY",
            "XAI_API_KEY",
            "LIGHTED_GROQ_API_KEY",
            "LIGHTED_GROK_API_KEY",
        ),
    )
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        validation_alias=AliasChoices(
            "GROQ_MODEL",
            "LIGHTED_GROQ_MODEL",
            "GROK_MODEL",
            "XAI_MODEL",
            "LIGHTED_GROK_MODEL",
        ),
    )
    preferred_provider: Literal["auto", "gemini", "groq", "grok"] = Field(
        default="auto",
        validation_alias=AliasChoices("LIGHTED_PROVIDER", "AI_PROVIDER", "LLM_PROVIDER"),
    )
    embedding_provider: Literal["gemini", "sentence-transformers"] = Field(
        default="gemini",
        validation_alias="LIGHTED_EMBEDDING_PROVIDER",
    )
    embedding_model: str = Field(
        default="gemini-embedding-001",
        validation_alias="LIGHTED_GEMINI_EMBEDDING_MODEL",
    )
    gemini_embedding_dimensions: int = Field(
        default=3072,
        validation_alias="LIGHTED_GEMINI_DIMENSIONS",
    )
    sentence_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="LIGHTED_SENTENCE_MODEL",
    )
    ai_data_dir: str = "./data"
    vector_store: str = "faiss"

    @property
    def data_path(self) -> Path:
        p = Path(self.ai_data_dir)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = AISettings()


def refresh_settings() -> AISettings:
    _load_project_env()
    global settings
    settings = AISettings()
    return settings


def get_api_key() -> str | None:
    _load_project_env()
    current = settings
    if current.gemini_api_key is None or not str(current.gemini_api_key).strip():
        current = refresh_settings()

    value = (
        current.gemini_api_key
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("LIGHTED_GEMINI_API_KEY")
    )
    if value is not None and not str(value).strip():
        return None
    return str(value) if value is not None else None


def get_grok_api_key() -> str | None:
    return get_groq_api_key()


def get_groq_api_key() -> str | None:
    _load_project_env()
    current = settings
    if current.groq_api_key is None or not str(current.groq_api_key).strip():
        current = refresh_settings()

    value = (
        current.groq_api_key
        or os.getenv("GROQ_API_KEY")
        or os.getenv("GROK_API_KEY")
        or os.getenv("XAI_API_KEY")
        or os.getenv("LIGHTED_GROQ_API_KEY")
        or os.getenv("LIGHTED_GROK_API_KEY")
    )
    if value is not None and not str(value).strip():
        return None
    return str(value) if value is not None else None
