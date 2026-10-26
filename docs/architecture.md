# LightEd Architecture

## High-level

```
┌──────────────┐      HTTPS       ┌──────────────┐      SQL       ┌──────────────┐
│  Next.js web │ ───────────────▶ │  FastAPI API │ ─────────────▶ │  PostgreSQL  │
│  (Vercel)    │   REST + JWT     │  (Render)    │                │  (managed)   │
└──────────────┘                  └──────┬───────┘                └──────────────┘
                                         │ Python import / HTTP
                                         ▼
                                  ┌──────────────┐
                                  │  ai/ module  │ ──▶ Gemini API (LLM + embeddings)
                                  │  (Render)    │ ──▶ FAISS / vector index
                                  └──────────────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │    Redis     │ (optional: cache + queue)
                                  └──────────────┘
```

## Monorepo layout

| Path          | Responsibility                                                        |
| ------------- | --------------------------------------------------------------------- |
| `apps/web`    | Next.js frontend — UI, dashboards, Chart.js visualizations            |
| `apps/api`    | FastAPI backend — REST API, JWT auth, RBAC, ORM models, migrations    |
| `ai`          | Pure-Python AI/ML — tutor, RAG, embeddings, analytics, planner        |
| `docs`        | Architecture, API reference, setup, roadmap                           |
| `infra`       | docker-compose + deploy configs (Render, Vercel)                      |
| `tests`       | Cross-cutting / end-to-end tests                                      |
| `.github`     | CI workflows, PR & issue templates                                    |

## Backend layers

```
app/
├── main.py          # FastAPI app, middleware, router registration
├── core/            # config (env), security (JWT + hashing)
├── db/              # engine, session, declarative Base
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response models
└── api/
    ├── deps.py      # auth + RBAC dependencies
    └── routes/      # auth, courses, quizzes, dashboard, ai
```

## Auth & roles

- JWT access token (short-lived) + refresh token (long-lived).
- Roles: `student`, `teacher`, `admin`.
- RBAC enforced via the `require_roles(...)` dependency factory.

## AI module design

- `gemini_client` isolates the provider (swap models without touching callers).
- `embeddings` + `retrieval` implement a minimal RAG loop (in-memory now, FAISS later).
- `weak_topics`, `performance`, `revision_planner` are classical-ML/heuristic and
  fully unit-tested without any API key.
- Everything degrades gracefully when `GEMINI_API_KEY` is missing.

## Data model (core)

```
User ──owns──▶ Course ──has──▶ Topic ──has──▶ Lesson ──has──▶ Quiz ──has──▶ Attempt
  │                                                                          ▲
  └──────────────────── Enrollment ─────────────────────────────────────────┘
                         (user ↔ course)                        (user ↔ quiz)
```
