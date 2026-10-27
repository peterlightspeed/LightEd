"""FastAPI application entrypoint.

On first boot in development we create tables and seed demo data so the app is
immediately usable. In production, run Alembic migrations and seed explicitly.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.routes import admin, ai, auth, courses, dashboard, lessons, planner, progress, quizzes, teacher
from app.core.config import settings

logger = logging.getLogger("lighted")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models so Base.metadata is populated before create_all.
    from app.db.session import Base, SessionLocal, engine
    from app.models.user import User

    Base.metadata.create_all(bind=engine)

    # Seed demo data in development, or in any env when SEED_ON_START=true.
    if settings.app_env == "development" or settings.seed_on_start:
        db = SessionLocal()
        try:
            # Seed when there are NO COURSES (not "no users"): an early sign-up must never
            # leave the catalogue empty. seed() is idempotent and get-or-creates demo users.
            from app.models.course import Course

            if db.scalar(select(Course).limit(1)) is None:
                from app.db.seed import seed

                seed()
                logger.info("Seeded demo data (catalogue was empty)")
        finally:
            db.close()
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    description="Backend for the LightEd personalized learning platform.",
    lifespan=lifespan,
)


@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    """Turn crashes into JSON 500s *inside* the CORS layer.

    Without this, an unhandled exception is answered by Starlette's outermost error
    handler, which has no CORS headers — the browser then reports a misleading
    "blocked by CORS policy" error instead of the real server error.
    This middleware is registered BEFORE CORSMiddleware so CORS wraps it.
    """
    try:
        return await call_next(request)
    except Exception:  # noqa: BLE001
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "Internal server error"}, status_code=500)


# Added last => outermost => every response (incl. errors + preflight) gets CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS allowed origins: %s (+ regex %s)", settings.cors_origins, settings.cors_origin_regex)

# Routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(lessons.router)
app.include_router(quizzes.router)
app.include_router(progress.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(ai.router)
app.include_router(teacher.router)
app.include_router(planner.router)


@app.get("/health", tags=["meta"])
def health():
    # cors_origins is shown on purpose: it makes CORS misconfiguration obvious at a glance.
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "cors_origins": settings.cors_origins,
        "google_enabled": bool(settings.google_client_id),
    }


@app.get("/", tags=["meta"])
def root():
    return {"message": "LightEd API", "docs": "/docs", "health": "/health"}
