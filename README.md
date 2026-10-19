# LightEd — AI-Powered Personalized Learning Platform

> Learn smarter, not harder. LightEd combines an AI tutor, personalized learning
> paths, auto-generated quizzes, progress tracking, and teacher analytics in one
> platform.

[![Frontend CI](https://github.com/your-org/lighted/actions/workflows/frontend-ci.yml/badge.svg)](../../actions)
[![Backend CI](https://github.com/your-org/lighted/actions/workflows/backend-ci.yml/badge.svg)](../../actions)
[![AI CI](https://github.com/your-org/lighted/actions/workflows/ai-ci.yml/badge.svg)](../../actions)

---

## ✨ Features

- **AI Tutor** — conversational help grounded in course material (RAG over course docs)
- **Personalized learning paths** — embeddings-based topic recommendations
- **Quiz generation** — auto-generate questions from lessons with the Gemini API
- **Progress tracking** — per-topic mastery, streaks, and completion
- **Teacher dashboards** — class-level analytics and at-risk student flags
- **Learning analytics** — weak-topic detection + simple performance prediction
- **Auth & roles** — JWT auth with student / teacher / admin role-based access

---

## 🧱 Tech Stack

| Layer      | Tech                                              |
| ---------- | ------------------------------------------------- |
| Frontend   | Next.js 14, React 18, TypeScript, Tailwind, Chart.js |
| Backend    | Python 3.11, FastAPI, SQLAlchemy, Pydantic        |
| AI / ML    | Python (Gemini API, FAISS, scikit-learn)          |
| Database   | PostgreSQL                                        |
| Cache/Queue| Redis (optional)                                  |
| Auth       | JWT (access + refresh)                            |
| DevOps     | Docker, Docker Compose, GitHub Actions            |
| Deploy     | Vercel (web), Render (api + ai), managed Postgres |

---

## 📁 Repository Layout

```
lighted/
├── apps/
│   ├── web/        # Next.js frontend (UI, dashboards, charts)
│   └── api/        # FastAPI backend (REST API, auth, DB)
├── ai/             # Python AI/ML module (tutor, RAG, analytics)
├── docs/           # Architecture, API, setup, roadmap
├── infra/          # docker-compose, deploy configs (render/vercel)
├── tests/          # Cross-cutting / e2e tests
├── .github/        # CI workflows, PR & issue templates
├── .env.example    # All required environment variables
└── README.md
```

See [`docs/architecture.md`](docs/architecture.md) for the full picture.

---

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose (recommended)
- A PostgreSQL database (local Docker or managed)
- A Gemini API key — https://aistudio.google.com/app/apikey

### 1. Clone & configure

```bash
git clone https://github.com/your-org/lighted.git
cd lighted
cp .env.example .env
# then edit .env and set JWT_SECRET_KEY + GEMINI_API_KEY at minimum
```

### 2. Run everything with Docker (easiest)

```bash
docker compose -f infra/docker-compose.yml up --build
```

- Frontend → http://localhost:3000
- Backend  → http://localhost:8000/docs
- Postgres → localhost:5432

### 3. Or run services manually

**Backend**

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head          # create tables
uvicorn app.main:app --reload --port 8000
```

**AI module** (importable library + optional service)

```bash
cd ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest              # sanity check
```

**Frontend**

```bash
cd apps/web
npm install
npm run dev                   # http://localhost:3000
```

---

## 🔐 Roles

| Role    | Can do                                                        |
| ------- | ------------------------------------------------------------ |
| student | Enroll, learn, take quizzes, view own progress + AI tutor     |
| teacher | Manage courses/topics/lessons, view class analytics           |
| admin   | Everything + user management                                  |

---

## 🧪 Testing

```bash
# Backend
cd apps/api && pytest

# AI
cd ai && pytest

# Frontend
cd apps/web && npm run lint && npm run typecheck
```

---

## 🌿 Git Workflow

We use a lightweight Git Flow:

- `main` — production-ready, protected
- `develop` — integration branch (default for PRs)
- `feature/*` — new work (branch from `develop`)
- `fix/*` — bug fixes
- `chore/*` — tooling / docs / infra

Commit style: **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 🗺️ Roadmap

Sprint 1 (Week 1) focus: **auth + course skeleton + AI tutor MVP + one dashboard.**
Full plan in [`docs/roadmap.md`](docs/roadmap.md).

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).
