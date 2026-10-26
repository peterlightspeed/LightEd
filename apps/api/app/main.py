"""FastAPI application entrypoint.

On first boot in development we create tables and seed demo data so the app is
immediately usable. In production, run Alembic migrations and seed explicitly.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.routes import admin, ai, auth, courses, dashboard, lessons, progress, quizzes
from app.core.config import settings

logger = logging.getLogger("lighted")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models so Base.metadata is populated before create_all.
    from app.db.session import Base, SessionLocal, engine
    from app.models.user import User

    Base.metadata.create_all(bind=engine)

    if settings.app_env == "development":
        db = SessionLocal()
        try:
            if db.scalar(select(User).limit(1)) is None:
                from app.db.seed import seed

                seed()
                logger.info("Seeded demo data")
        finally:
            db.close()
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    description="Backend for the LightEd personalized learning platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(lessons.router)
app.include_router(quizzes.router)
app.include_router(progress.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(ai.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/", tags=["meta"])
def root():
    return {"message": "LightEd API", "docs": "/docs", "health": "/health"}
