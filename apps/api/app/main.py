from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai, auth, courses, dashboard, quizzes
from app.core.config import settings

app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    description="Backend for the LightEd personalized learning platform.",
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
app.include_router(quizzes.router)
app.include_router(dashboard.router)
app.include_router(ai.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/", tags=["meta"])
def root():
    return {"message": "LightEd API", "docs": "/docs"}
