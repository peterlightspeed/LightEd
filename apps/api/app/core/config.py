"""Application configuration.

All values come from environment variables (or a local `.env` file).
The defaults are intentionally *runnable*: if no DATABASE_URL is supplied we
fall back to a local SQLite file so a reviewer can boot the API in seconds.
Production should always set DATABASE_URL to a PostgreSQL DSN.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ---- General -----------------------------------------------------------
    app_name: str = "LightEd"
    app_env: str = "development"  # development | staging | production
    log_level: str = "INFO"

    # ---- Security ----------------------------------------------------------
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h for the demo; shorten in prod
    refresh_token_expire_days: int = 7

    # ---- CORS --------------------------------------------------------------
    # Comma-separated list. The Next.js dev server is allowed by default.
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Your deployed frontend, e.g. https://light-ed.vercel.app (also allowed by CORS).
    frontend_url: str | None = None
    # Safety net: any *.vercel.app origin (production + preview deploys) is allowed
    # by default so a mistyped BACKEND_CORS_ORIGINS can never lock you out again.
    # Set to an empty string to disable.
    cors_origin_regex: str = r"https://.*\.vercel\.app"

    # ---- First-boot seeding ------------------------------------------------
    # Render's free tier has no shell, so set SEED_ON_START=true once to create the
    # demo users/courses automatically when the database is empty. Safe to leave on:
    # it only seeds an EMPTY users table.
    seed_on_start: bool = False

    # ---- Database ----------------------------------------------------------
    # Postgres in production, SQLite for a zero-setup local demo.
    database_url: str = "sqlite:///./lighted.db"

    # ---- AI (optional, kept separate from the core app) --------------------
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    ai_service_url: str | None = None

    # ---- Auth providers (placeholders for later integration) ---------------
    google_client_id: str | None = None
    google_client_secret: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        """Normalised origin list: trims spaces/quotes and trailing slashes.

        A trailing slash (https://x.vercel.app/) is the #1 cause of CORS failures,
        because browsers send the Origin header WITHOUT it.
        """
        raw = self.backend_cors_origins.split(",")
        if self.frontend_url:
            raw.append(self.frontend_url)
        origins = []
        for o in raw:
            o = o.strip().strip("\"'").rstrip("/")
            if o and o not in origins:
                origins.append(o)
        return origins

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def sqlalchemy_url(self) -> str:
        """Normalise common Postgres URL formats to the psycopg v3 driver."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
