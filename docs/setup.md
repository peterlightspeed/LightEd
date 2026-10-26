# Setup Guide

## 1. Prerequisites

- Node.js 20+, npm
- Python 3.11+
- Docker + Docker Compose (recommended)
- PostgreSQL 15+ (or use the Docker one)
- Gemini API key — https://aistudio.google.com/app/apikey

## 2. Environment

```bash
cp .env.example .env
```

Set at minimum:
- `JWT_SECRET_KEY` — generate with
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `GEMINI_API_KEY` — from Google AI Studio

## 3. Option A — Docker (everything)

```bash
docker compose -f infra/docker-compose.yml up --build
```

| Service  | URL                          |
| -------- | ---------------------------- |
| Web      | http://localhost:3000        |
| API      | http://localhost:8000/docs   |
| Postgres | localhost:5432               |
| Redis    | localhost:6379               |

## 4. Option B — Run each service manually

### Backend

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic revision --autogenerate -m "init schema"   # first time only
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### AI module

```bash
cd ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

### Frontend

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
```

## 5. Common tasks

| Task                  | Command                                   |
| --------------------- | ----------------------------------------- |
| Run all tests         | `make test`                               |
| Lint everything       | `make lint`                               |
| Format Python         | `make format`                             |
| Start full stack      | `make up`                                 |

## 6. Troubleshooting

- **CORS errors** → check `BACKEND_CORS_ORIGINS` includes your web URL.
- **401 on API calls** → token missing/expired; re-login.
- **AI returns fallback text** → `GEMINI_API_KEY` not set (features still work offline).
- **DB connection refused** → Postgres not up; check `DATABASE_URL`.
