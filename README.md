# LightEd — AI-Assisted Personalized Learning Platform

> **Light yourself. Learn at your pace.**
> A working MVP built from the LightEd Figma design for the TechCrush Buildathon.

LightEd is a full-stack learning platform with three roles — **student**, **teacher** and
**admin** — covering course discovery, lessons, quizzes, progress tracking and class
analytics. The frontend is a pixel-faithful recreation of the supplied Figma screens;
the backend is a real FastAPI + SQLAlchemy service with JWT auth and seeded demo data.

---

## What actually works (shipped MVP)

| Area | Status | Notes |
| --- | --- | --- |
| Landing page | ✅ | Hero, features, how-it-works, for-teachers, CTA, footer |
| Auth | ✅ | Register (role select), login, forgot-password (stub), JWT access + refresh |
| Google Auth | 🟡 Placeholder | `/auth/google` returns `501` with integration notes — see GUIDE.md |
| Student dashboard | ✅ | Progress ring, streak, continue-learning, focus areas, recommendations |
| Teacher dashboard | ✅ | Class stats, course progress, at-risk students, full roster table |
| Admin shell | ✅ | User list with role change, course publish/unpublish |
| Course catalogue | ✅ | Search + subject + level filters, enrollment state |
| Course detail | ✅ | Curriculum accordion, enrol button, per-lesson completion |
| Lesson view | ✅ | Rich text content, prev/next, mark complete, quiz link |
| Quiz | ✅ | Question flow, server-side grading, per-question explanations, retry |
| Progress / analytics | ✅ | Completion ring, course breakdown, recent lessons timeline |
| AI tutor | 🟡 Stub | `POST /ai/tutor` returns a canned, clearly-labelled placeholder reply |

### Deliberately **not** in this MVP

These were in the original concept doc but are **not implemented**, and the UI does not
pretend they are: RAG over course documents, embeddings-based recommendations, Gemini
quiz generation, FAISS vector search, Redis queues, and ML performance prediction. The
recommendations on the student dashboard are rule-based (lowest mastery first) and the
focus areas come from real quiz/lesson data. See `GUIDE.md → Roadmap` for how to add them.

---

## Tech stack

| Layer | Tech |
| --- | --- |
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS 3, lucide-react |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (typed), Pydantic v2 |
| Database | PostgreSQL in production · SQLite fallback for zero-config local demo |
| Auth | JWT (access + refresh), bcrypt password hashing |
| AI / ML | Separate `ai/` Python package (stub service today) |
| DevOps | Docker + Docker Compose, GitHub Actions, Makefile |

No chart library: the progress rings are inline SVG and the weekly chart is CSS bars,
so the bundle stays small (≈87 kB shared JS).

---

## Quick start (2 terminals, ~2 minutes)

### 1. Backend

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On first boot the API creates `lighted.db` (SQLite) and **auto-seeds** demo data.
Interactive docs: <http://localhost:8000/docs>

### 2. Frontend

```bash
cd apps/web
npm install
cp .env.local.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open <http://localhost:3000>.

### Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Student | `student@lighted.dev` | `password123` |
| Teacher | `teacher@lighted.dev` | `password123` |
| Admin | `admin@lighted.dev` | `password123` |

The student account is pre-loaded with 7 of 9 lessons complete, quiz attempts and a
streak so every dashboard has meaningful data on first load.

---

## Repository layout

```
lighted/
├── apps/
│   ├── web/                     # Next.js 14 frontend
│   │   └── src/
│   │       ├── app/
│   │       │   ├── page.tsx                 # Landing
│   │       │   ├── (auth)/                  # login, register, forgot-password
│   │       │   └── (app)/                   # dashboard, courses, lessons, quizzes, progress
│   │       ├── components/
│   │       │   ├── ui.tsx                   # Design-system primitives
│   │       │   ├── layout/AppShell.tsx      # Sidebar + topbar shell
│   │       │   └── marketing/               # Nav + Footer
│   │       ├── lib/                         # api client, auth, auth-context, utils
│   │       └── types/index.ts               # Shared API types
│   └── api/                     # FastAPI backend
│       └── app/
│           ├── main.py                      # App factory, CORS, lifespan seed
│           ├── core/                        # config, security
│           ├── db/                          # session, seed
│           ├── models/                      # SQLAlchemy models
│           ├── schemas/                     # Pydantic schemas
│           ├── services/learning.py         # Shared learning-domain helpers
│           └── api/routes/                  # auth, courses, lessons, quizzes, progress, dashboard, admin, ai
├── ai/                          # Separate AI/ML package (stub tutor service)
├── docs/                        # api.md, architecture.md, setup.md, roadmap.md
├── infra/                       # Docker + compose
├── tests/                       # Backend smoke tests
├── GUIDE.md                     # ⭐ Setup, config, deploy, git, troubleshooting
├── todo.md                      # Build checklist (all ticked)
├── Makefile
└── .env.example
```

---

## API surface (summary)

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register` | – | Create account (role: student/teacher) |
| POST | `/auth/login` | – | Get access + refresh token |
| GET | `/auth/me` | user | Current profile |
| POST | `/auth/refresh` | – | Exchange refresh token |
| POST | `/auth/forgot-password` | – | Always-200 stub |
| POST | `/auth/google` | – | `501` placeholder |
| GET | `/courses` | optional | Catalogue (published only for anon) |
| GET | `/courses/mine` | user | Courses I own/teach |
| POST | `/courses` | teacher/admin | Create course |
| GET | `/courses/{id}` | optional | Detail + curriculum + enrollment state |
| POST | `/courses/{id}/enroll` | user | Idempotent enroll |
| GET | `/lessons/{id}` | user | Lesson detail |
| POST | `/lessons/{id}/complete` | user | Idempotent completion |
| GET | `/quizzes/lesson/{lesson_id}` | user | Quiz for a lesson |
| GET | `/quizzes/{id}` | user | Quiz **without** answer keys |
| POST | `/quizzes/{id}/attempts` | user | Submit answers → graded result |
| GET | `/progress/me` | user | Full progress payload |
| GET | `/dashboard/student` | student | Student dashboard payload |
| GET | `/dashboard/teacher` | teacher/admin | Class analytics |
| GET | `/dashboard/admin` | admin | Platform stats |
| GET | `/admin/users` | admin | All users |
| PATCH | `/admin/users/{id}/role` | admin | Change role |
| PATCH | `/admin/courses/{id}/publish` | admin | Publish / unpublish |
| POST | `/ai/tutor` | user | Stub tutor reply |

Full request/response schemas: `docs/api.md` and `/docs` (Swagger).

---

## Docker

```bash
cp .env.example .env          # then edit JWT_SECRET_KEY
docker compose -f infra/docker-compose.yml up --build
```

Web → <http://localhost:3000>, API → <http://localhost:8000>, Postgres → `localhost:5432`.

---

## Verification done

- Backend: every endpoint exercised with `fastapi.testclient` against a fresh DB.
- Frontend: `npm run build` passes with all 12 routes, zero type errors.
- Manual E2E in Chromium: login as all three roles → dashboard → course → lesson →
  quiz → progress, plus register and forgot-password.

---

## Documentation

- **[GUIDE.md](GUIDE.md)** — step-by-step setup, env vars, Postgres switch, deployment
  (Vercel + Render), git commands, Google Auth integration, troubleshooting.
- **[todo.md](todo.md)** — the build checklist.
- **[docs/api.md](docs/api.md)** — endpoint reference.
- **[docs/architecture.md](docs/architecture.md)** — how the pieces fit.

## License

MIT — see [LICENSE](LICENSE).


---

## Support

Email **lightedsupport@gmail.com** · Phone **0810 882 1809**

Deploy/CORS problems: [FIX_BACKEND.md](FIX_BACKEND.md) · Google sign-in: [GOOGLE_AUTH.md](GOOGLE_AUTH.md)
