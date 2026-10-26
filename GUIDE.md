# LightEd — Operator's Guide

Everything **you** need to do to run, configure, push and deploy this project.
Written for someone who has never opened the repo before.

If you only read one section, read **1. Run it locally**. It takes about two minutes.

---

## Contents

1. [Run it locally](#1-run-it-locally)
2. [Environment variables](#2-environment-variables)
3. [Switching to PostgreSQL](#3-switching-to-postgresql)
4. [Docker](#4-docker)
5. [Git: from zero to first push](#5-git-from-zero-to-first-push)
6. [Deploying to production](#6-deploying-to-production)
7. [Google Auth integration](#7-google-auth-integration)
8. [Wiring the AI tutor (Gemini)](#8-wiring-the-ai-tutor-gemini)
9. [Troubleshooting](#9-troubleshooting)
10. [Assumptions made in this MVP](#10-assumptions-made-in-this-mvp)
11. [Roadmap: what to build next](#11-roadmap-what-to-build-next)

---

## 1. Run it locally

### Prerequisites

| Tool | Version | Check |
| --- | --- | --- |
| Python | 3.11+ | `python --version` |
| Node.js | 18+ (20 recommended) | `node --version` |
| npm | 9+ | `npm --version` |
| Git | any | `git --version` |

PostgreSQL is **not** required for local development — the API falls back to SQLite
automatically. That is the fastest path to a running demo.

### Terminal 1 — API

```bash
cd apps/api

# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows PowerShell

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

What you should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

On the very first boot the app creates `apps/api/lighted.db`, creates all tables and
runs the seed script (users, 4 courses, 9 lessons, quizzes, attempts, progress).

Sanity check: <http://localhost:8000/health> should return
`{"status":"ok","app":"LightEd","env":"development"}`.

### Terminal 2 — Web

```bash
cd apps/web
npm install
cp .env.local.example .env.local
npm run dev
```

Open <http://localhost:3000>.

### Log in

| Role | Email | Password | Lands on |
| --- | --- | --- | --- |
| Student | `student@lighted.dev` | `password123` | `/dashboard` |
| Teacher | `teacher@lighted.dev` | `password123` | `/dashboard/teacher` |
| Admin | `admin@lighted.dev` | `password123` | `/dashboard/admin` |

### Reset the demo data

Stop the API, delete the database, start it again:

```bash
rm apps/api/lighted.db
uvicorn app.main:app --reload --port 8000    # re-seeds automatically
```

The seed only runs when the `users` table is empty, so deleting the file is the clean
way to start over.

---

## 2. Environment variables

### Backend — `apps/api/.env` (optional)

The backend works with **no** `.env` file at all (sane defaults + SQLite). Create one
when you want to change something. Copy from the repo root `.env.example`.

| Variable | Default | What it does |
| --- | --- | --- |
| `APP_ENV` | `development` | `development` enables auto-seed and verbose errors |
| `DATABASE_URL` | `sqlite:///./lighted.db` | Any SQLAlchemy URL. `postgres://` is auto-normalised |
| `JWT_SECRET_KEY` | `dev-secret-change-me` | **Change this in production.** Signs all tokens |
| `JWT_ALGORITHM` | `HS256` | Leave as is unless you know why |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `GEMINI_API_KEY` | empty | Only needed when you wire the real AI tutor |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | empty | Only needed for Google login |
| `AI_SERVICE_URL` | empty | URL of the separate `ai/` service |

Generate a strong secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Frontend — `apps/web/.env.local`

| Variable | Example | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | **No trailing slash.** Must be reachable from the browser |
| `NEXT_PUBLIC_APP_NAME` | `LightEd` | Shown in a few places |

Anything prefixed `NEXT_PUBLIC_` is baked into the client bundle at build time. Never put
secrets there.

> **Deployment gotcha:** if `NEXT_PUBLIC_API_URL` still points at `localhost`, the
> deployed site will fail every request. Set it to your public API URL *before* building.

---

## 3. Switching to PostgreSQL

SQLite is great for the demo and terrible for production (single writer, no concurrent
migrations). Switching is a one-line change.

### Local Postgres

```bash
createdb lighted
export DATABASE_URL="postgresql+psycopg://localhost:5432/lighted"
```

Note the `+psycopg` driver suffix — the project uses psycopg 3. Plain `postgresql://` and
Heroku-style `postgres://` are also accepted and rewritten internally.

### Hosted Postgres (Neon / Supabase / Render)

Copy the connection string from the provider dashboard and set it as `DATABASE_URL`.
If the provider gives you `postgres://user:pass@host/db`, use it as-is.

### Creating the tables

Tables are created automatically on startup via `Base.metadata.create_all`. For a real
production rollout you should switch to Alembic migrations:

```bash
cd apps/api
pip install alembic
alembic init migrations
# point migrations/env.py at app.db.session.Base and app.core.config.settings
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### Seeding production

Auto-seed is gated on `APP_ENV == "development"`. To seed a production database
deliberately:

```bash
cd apps/api
APP_ENV=development python -m app.db.seed
```

Then set `APP_ENV=production` on the running service so it stops re-seeding.

---

## 4. Docker

```bash
cp .env.example .env
# edit JWT_SECRET_KEY at minimum

docker compose -f infra/docker-compose.yml up --build
```

| Service | Port | Notes |
| --- | --- | --- |
| `web` | 3000 | Next.js production build |
| `api` | 8000 | Uvicorn, 2 workers |
| `db` | 5432 | Postgres 16, volume-backed |

Tear down: `docker compose -f infra/docker-compose.yml down`
Tear down **and wipe data**: add `-v`.

---

## 5. Git: from zero to first push

The repo is already `git init`-ed. These are the exact commands to get it onto GitHub.

### Option A — brand new GitHub repo

1. Create an empty repo on GitHub (no README, no .gitignore — you already have both).
2. Then:

```bash
cd lighted
git add -A
git commit -m "feat: LightEd MVP — auth, courses, lessons, quizzes, dashboards"
git branch -M main
git remote add origin https://github.com/<your-username>/lighted.git
git push -u origin main
```

### Option B — repo already exists on GitHub

```bash
cd lighted
git remote add origin https://github.com/<your-username>/lighted.git
git fetch origin
git branch -M main
git add -A
git commit -m "feat: LightEd MVP — auth, courses, lessons, quizzes, dashboards"
git push -u origin main --force
```

Only force-push if you are certain the remote has nothing you need.

### If you use SSH

```bash
git remote add origin git@github.com:<your-username>/lighted.git
```

### Before you commit — check nothing secret is staged

```bash
git status
git diff --cached --name-only | grep -E '\.env$|\.db$|node_modules|\.venv'
```

That command should print **nothing**. `.gitignore` already covers `.env`, `*.db`,
`node_modules/`, `.venv/`, `__pycache__/`, `.next/`.

### Suggested commit sequence

If you prefer to push in logical chunks rather than one big commit:

```bash
git add apps/api && git commit -m "feat(api): FastAPI backend — models, auth, learning endpoints, seed"
git add apps/web/src/lib apps/web/src/types apps/web/src/components/ui.tsx \
  && git commit -m "feat(web): design tokens, API client, auth context, UI primitives"
git add apps/web/src/app/page.tsx apps/web/src/components/marketing \
  && git commit -m "feat(web): landing page"
git add "apps/web/src/app/(auth)" && git commit -m "feat(web): login, register, forgot password"
git add "apps/web/src/app/(app)" && git commit -m "feat(web): dashboards, courses, lessons, quizzes, progress"
git add README.md GUIDE.md todo.md docs .env.example \
  && git commit -m "docs: README, operator guide, API reference"
```

### Commit message conventions used here

`type(scope): summary` — types are `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
Keep the summary under ~72 characters and in the imperative mood ("add", not "added").

---

## 6. Deploying to production

Recommended split: **Vercel** for the Next.js app, **Render** (or Railway/Fly) for the
FastAPI service, **Neon** (or Supabase) for Postgres. All three have free tiers.

### 6a. Database — Neon

1. Create a project at <https://neon.tech>.
2. Copy the connection string. It looks like
   `postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require`.
3. Keep it for the API step. Add `?sslmode=require` if it is missing.

### 6b. API — Render

1. **New → Web Service**, connect your GitHub repo.
2. Settings:
   - **Root directory:** `apps/api`
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Environment variables:

```
APP_ENV=production
DATABASE_URL=<your Neon connection string>
JWT_SECRET_KEY=<48-char random string>
BACKEND_CORS_ORIGINS=https://your-app.vercel.app
```

4. Deploy. Note the URL, e.g. `https://lighted-api.onrender.com`.
5. Verify: `https://lighted-api.onrender.com/health`.

> Render's free tier sleeps after inactivity — the first request after a nap takes ~30s.
> That is expected, not a bug.

### 6c. Web — Vercel

1. **Add New → Project**, import the repo.
2. **Root Directory:** `apps/web`
3. Framework preset: Next.js (auto-detected).
4. Environment variable:

```
NEXT_PUBLIC_API_URL=https://lighted-api.onrender.com
```

5. Deploy.

### 6d. Close the loop

Go back to Render and update `BACKEND_CORS_ORIGINS` to your real Vercel URL
(`https://lighted.vercel.app`). Redeploy the API. Without this the browser will block
every request with a CORS error.

### 6e. Post-deploy checklist

- [ ] `GET /health` returns ok
- [ ] `GET /courses` returns the 4 seeded courses
- [ ] Login as `student@lighted.dev` works on the deployed site
- [ ] Dashboard loads data (proves CORS + API URL are right)
- [ ] Browser console has no red errors
- [ ] `JWT_SECRET_KEY` is **not** the default value

### 6f. Alternative: single-host deploy

If you would rather run everything on one box, use the Docker Compose file on any VPS
with a reverse proxy (Caddy is the least work). Point `NEXT_PUBLIC_API_URL` at
`https://api.yourdomain.com` and rebuild the web image.

---

## 7. Google Auth integration

**Implemented.** Backend `POST /auth/google` verifies the Google ID token and returns the normal
JWT; the frontend shows the official Google button on Login/Register once a client ID exists.
Setup (5 minutes) is in **[GOOGLE_AUTH.md](GOOGLE_AUTH.md)**.

## 8. Wiring the AI tutor (Gemini)

`POST /ai/tutor` currently returns a fixed, clearly-labelled placeholder. To make it real:

1. Get a key at <https://aistudio.google.com/app/apikey>.
2. `pip install google-generativeai` in `apps/api`.
3. In `app/api/routes/ai.py`, replace the stub body:

```python
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)

response = model.generate_content(
    f"You are a patient tutor. Course context:\n{context}\n\nStudent asks: {payload.message}"
)
return {"reply": response.text}
```

4. Pass the lesson's `content` as `context` so answers stay grounded in course material.
5. Keep the endpoint behind `get_current_user` — it costs money per call.

The `ai/` folder is deliberately a separate package so you can move this into its own
service later without touching the main API.

---

## 9. Troubleshooting

> **CORS error on the deployed site, `externally-managed-environment`, or empty-DB 401s?** See **[FIX_BACKEND.md](FIX_BACKEND.md)**.

### `ModuleNotFoundError: No module named 'app'`

You are not in `apps/api`, or the venv is not active. `cd apps/api && source .venv/bin/activate`.

### `[Errno 98] address already in use`

Something is already on port 8000.

```bash
lsof -ti:8000 | xargs kill -9      # macOS / Linux
netstat -ano | findstr :8000       # Windows, then taskkill /PID <pid> /F
```

Or just use another port: `uvicorn app.main:app --reload --port 8001` and update
`NEXT_PUBLIC_API_URL`.

### Frontend shows empty dashboards / network errors

1. Is the API actually running? `curl http://localhost:8000/health`
2. Does `apps/web/.env.local` exist and contain `NEXT_PUBLIC_API_URL=http://localhost:8000`?
3. Did you restart `npm run dev` after editing `.env.local`? Next.js only reads env at boot.
4. Check the browser Network tab — a CORS error means `BACKEND_CORS_ORIGINS` is wrong.

### `401 Unauthorized` on every request after a restart

Changing `JWT_SECRET_KEY` invalidates all existing tokens. Log out and back in.

### `useSearchParams() should be wrapped in a suspense boundary`

Already handled in `login/page.tsx` — if you add another page that reads query params,
wrap the component in `<Suspense>` the same way.

### `npm run build` fails with type errors

```bash
cd apps/web
npx tsc --noEmit        # see the real errors
rm -rf .next && npm run build
```

### Postgres: `password authentication failed`

The password in `DATABASE_URL` must be URL-encoded if it contains `@`, `:`, `/` or `#`.
Use `urllib.parse.quote_plus` on the password portion.

### Seed did not run

The seed is skipped when users already exist, and when `APP_ENV != "development"`.
Delete `lighted.db` (SQLite) or truncate `users` (Postgres), then restart.

### Quiz page shows "No quiz for this lesson"

Only some seeded lessons have quizzes. That is intentional — the button is hidden when
no quiz exists, so hitting this message means a stale link.

---

## 10. Assumptions made in this MVP

The Figma export did not specify everything, so these were decided and are worth knowing:

1. **Roles are chosen at registration** (student or teacher). Admin accounts are
   seed-only — there is no self-serve admin signup, which is the safe default.
2. **Quizzes are one-per-lesson**, attached to the lesson rather than the course.
3. **Grading is server-side.** `answer_index` is never sent to the client before
   submission, so the quiz cannot be cheated from the network tab.
4. **Pass mark is 70%**, shown as a pass/fail badge on the results screen.
5. **Enrollment is idempotent** — clicking Enrol twice does not duplicate the row
   (enforced by a unique constraint).
6. **Lesson completion is idempotent** for the same reason.
7. **"Streak" is a simple consecutive-day counter** based on lesson completion
   timestamps, not a full activity calendar.
8. **Recommendations are rule-based** — the student dashboard surfaces the courses with
   the lowest completion first. No embeddings, no ML model.
9. **Focus areas** are derived from real per-course average scores, bucketed into
   needs work / developing / strong.
10. **The AI tutor is a labelled stub.** It does not call an LLM yet.
11. **Charts are CSS/SVG**, not Chart.js — smaller bundle, no runtime dependency.
12. **Teachers see all students**, not just their own classes. Course ownership exists in
    the data model (`owner_id`), but the teacher dashboard is platform-wide for the demo.
13. **No email is actually sent** by forgot-password; it always returns 200 to avoid
    leaking which emails exist.
14. **No refresh-token rotation or revocation list.** Acceptable for an MVP, not for
    handling real money or PII at scale.

---

## 11. Roadmap: what to build next

Roughly in order of value-per-hour:

1. **Real AI tutor** — Gemini + lesson context (section 8). Biggest visible win.
2. **Teacher course ownership** — filter the teacher dashboard by `owner_id`, add a
   "create course" form in the UI (the API endpoint already exists).
3. **Google Auth** — section 7. Removes the signup friction.
4. **Alembic migrations** — replace `create_all` before you have real users.
5. **Refresh-token rotation + logout revocation** — a `token_version` column on `user`.
6. **File uploads for lessons** — S3/R2 for images and PDFs, then a real rich-text editor.
7. **Quiz authoring UI** — currently quizzes only come from the seed script.
8. **Search across lessons** — Postgres full-text search is enough at this scale.
9. **Email delivery** — Resend or Postmark for real password resets.
10. **Rate limiting** — especially on `/auth/login` and `/ai/tutor`.
11. **Tests** — the repo has a smoke-test scaffold in `tests/`; grow it into real
    coverage of the auth and grading paths first.
12. **Accessibility pass** — focus traps in the mobile drawer, aria labels on icon
    buttons, colour-contrast audit on the gold accents.

---

## Need to change something fast?

| I want to… | Edit this |
| --- | --- |
| Change brand colours | `apps/web/tailwind.config.ts` (`navy`, `brand`, `gold`) |
| Change the logo | `Logo` in `apps/web/src/components/ui.tsx` |
| Change sidebar links | `NAV` array in `apps/web/src/components/layout/AppShell.tsx` |
| Add demo courses/lessons | `apps/api/app/db/seed.py` |
| Change pass mark | `apps/api/app/api/routes/quizzes.py` (`>= 70`) |
| Add a dashboard stat | route in `apps/api/app/api/routes/dashboard.py` + type in `apps/web/src/types/index.ts` |
| Change token lifetime | `ACCESS_TOKEN_EXPIRE_MINUTES` env var |
