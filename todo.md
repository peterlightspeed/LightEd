# LightEd MVP — Build Todo

> Working checklist for the buildathon MVP. All items verified.

## 0. Repo & foundations
- [x] Audit uploaded Figma screenshots + existing scaffold
- [x] Copy scaffold to working repo, init git
- [x] Design tokens (navy / blue / gold / lavender) in Tailwind + globals
- [x] Shared TypeScript types + API client + auth helpers

## 1. Backend (FastAPI)
- [x] Config supports Postgres (prod) and SQLite (local demo) automatically
- [x] Models: User, Course, Topic, Lesson, Quiz, Attempt, Enrollment, Progress
- [x] Schemas for all request/response bodies
- [x] Auth: register, login, me, refresh, forgot-password placeholder, Google placeholder
- [x] Courses: list, detail (with curriculum), create, enroll
- [x] Lessons: detail, complete
- [x] Quizzes: by lesson, get, submit attempt, my attempts
- [x] Progress + analytics endpoint
- [x] Dashboard: student, teacher, admin stats
- [x] AI tutor stub endpoint (separate `ai/` package)
- [x] Seed script with demo teacher/student/admin + realistic course data
- [x] Smoke-test all endpoints with httpx/TestClient

## 2. Frontend (Next.js)
- [x] UI primitives: Button, Input, Card, Badge, ProgressBar, ProgressRing, Select, Avatar, EmptyState
- [x] Layout: marketing nav/footer, auth shell, app shell (sidebar + topbar)
- [x] Landing page
- [x] Login, Register (role select), Forgot password
- [x] Student dashboard (progress, focus areas, recommendations, AI tutor card)
- [x] Teacher dashboard (class stats, students at risk, courses)
- [x] Course list + course detail (curriculum accordion)
- [x] Lesson view (content, mark complete, next)
- [x] Quiz page (question flow, results, retry)
- [x] Progress / analytics page (charts)
- [x] Admin shell (users, courses overview)
- [x] Responsive pass + loading/empty/error states

## 3. Verification
- [x] Backend runs, seed succeeds, endpoints return data
- [x] Frontend builds (`npm run build`) with no type errors
- [x] End-to-end demo flow: login → dashboard → course → lesson → quiz → progress
- [x] Screenshots captured for delivery

## 4. Docs & handoff
- [x] README with quick start
- [x] GUIDE.md (setup, config, deploy, git prompts, troubleshooting)
- [x] docs/api.md updated
- [x] .env.example complete
- [x] Git commands + first commit message

## 5. Known follow-ups (not blocking the MVP)
- [ ] Wire real Gemini tutor (`GUIDE.md` § 8)
- [x] Google OAuth — done; just add `GOOGLE_CLIENT_ID` (see GOOGLE_AUTH.md)
- [ ] Alembic migrations before real users
- [ ] Quiz authoring UI (quizzes currently seed-only)
- [ ] Teacher scoping by `owner_id`

## 6. v2 additions (this release)
- [x] Production CORS fix (normalised origins, `FRONTEND_URL`, vercel regex, CORS on 500s)
- [x] `SEED_ON_START` for hosts without a shell; Python-3.13-safe requirements; `.python-version`
- [x] Real LightEd logo everywhere + favicon/apple-icon/OG image
- [x] Google sign-in (backend verify + frontend button)
- [x] Guided product tour (auto on first login, replay via the ? button)
- [x] Support email + phone (landing, footer, auth pages, account menu)
- [x] Cold-start resilience (warm-up ping, retries, "waking up" hint)
- [ ] YOU: set Render env vars + redeploy (FIX_BACKEND.md), create Google client ID (GOOGLE_AUTH.md)
- [ ] Real password-reset emails (`/auth/forgot-password` is still a stub)
- [ ] Alembic migrations before real users (tables are created with `create_all` today)
