import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    embedding_model: str = "text-embedding-004"
    ai_data_dir: str = "./data"
    vector_store: str = "faiss"

    @property
    def data_path(self) -> Path:
        p = Path(self.ai_data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = AISettings()


def get_api_key() -> str | None:
    return settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
