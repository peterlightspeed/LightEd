from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # General
    app_name: str = "LightEd"
    app_env: str = "development"
    log_level: str = "INFO"

    # Security
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # CORS
    backend_cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+psycopg://lighted:lighted@localhost:5432/lighted"

    # Redis (optional)
    redis_url: str | None = None

    # AI
    gemini_api_key: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
