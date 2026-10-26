# DEPLOY.md — LightEd to production

The stack: **Neon** (Postgres) → **Render** (FastAPI) → **Vercel** (Next.js).

Do the steps **in this order**. Each one depends on the URL from the previous step.

| Step | Service | What you get | Cost |
| --- | --- | --- | --- |
| 1 | [Neon](https://neon.tech) | Managed Postgres | Free |
| 2 | [Render](https://render.com) | FastAPI backend | Free |
| 3 | Seed the DB | Demo users + courses | — |
| 4 | [Vercel](https://vercel.com) | Next.js frontend | Free |

Total time: ~20 minutes. No credit card on any of them.

---

## ⚠️ Read this first — the one thing that will break your deploy

In `apps/api/app/main.py`:

```python
if settings.app_env == "development":
    ...seed demo data...
```

Tables are **always** created (`Base.metadata.create_all`), but **demo data is only
seeded in development**. If you deploy with `APP_ENV=production` and skip Step 3, your
database will be empty and every login will return `401`.

Step 3 is not optional. Do not skip it.

---

## Step 1 — Neon (database)

1. Sign up at <https://neon.tech> → **Create project**.
2. Name: `lighted`. Region: closest to you. Postgres version: default (16/17).
3. On the dashboard, open **Connection string** and copy it. It looks like:

```
postgresql://neondb_owner:AbC123xyz@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

4. Save it somewhere. That is your `DATABASE_URL`.

**Notes**
- Use the **direct** connection string (no `-pooler` in the host) for simplicity. The
  pooled one also works.
- Keep `?sslmode=require` on the end. Neon requires TLS.
- Your code auto-rewrites `postgresql://` → `postgresql+psycopg://`, so paste it
  **exactly as Neon gives it**. Do not edit the prefix.

---

## Step 2 — Render (backend API)

1. Sign up at <https://render.com> with GitHub.
2. **New +** → **Web Service** → connect your `lighted` repo.
3. Fill in exactly:

| Field | Value |
| --- | --- |
| Name | `lighted-api` |
| Region | same as Neon if possible |
| Branch | `main` |
| **Root Directory** | `apps/api` |
| Runtime | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Instance Type | Free |

> The start command **must** use `$PORT`. Render assigns the port dynamically; hardcoding
> `8000` will fail the health check.

> ### ⚠️ "I don't see Runtime / Build Command / Start Command"
>
> Render scans the repo and, if it finds a `Dockerfile`, auto-selects
> **Language: Docker**. That swaps the Python fields for Docker fields
> (Dockerfile Path, Docker Command, Build Context).
>
> **Fix — Option A (recommended):** change the **Language** dropdown to **Python 3**.
> The Build Command and Start Command fields appear immediately, and you can ignore
> every Docker field on the page.
>
> **Option B (stay on Docker):** the `Dockerfile` in this repo now reads `$PORT` and
> defaults to 8000, so it works as-is. Set:
>
> | Docker field | Value |
> | --- | --- |
> | Docker Build Context Directory | `apps/api` |
> | Dockerfile Path | `apps/api/Dockerfile` |
> | Docker Command | *(leave blank — the CMD in the image is correct)* |
>
> Both paths are valid. Option A builds faster and gives you a Shell tab for seeding;
> **on the free Docker plan there is no Shell**, so you'd have to seed via a one-off
> job or by temporarily setting `APP_ENV=development`. Use Option A.

4. Scroll to **Environment Variables** and add these:

| Key | Value | Notes |
| --- | --- | --- |
| `PYTHON_VERSION` | `3.11.9` | **Important.** Without it Render may pick 3.13 and your pinned wheels won't build |
| `APP_ENV` | `production` | Turns off auto-seed and verbose errors |
| `DATABASE_URL` | your Neon string | Paste exactly, keep `?sslmode=require` |
| `JWT_SECRET_KEY` | 48-char random string | Generate below |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | **Temporary** — replaced in Step 5 |

Generate the secret (run locally):

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

5. **Create Web Service**. First build takes 3–5 minutes.

6. When it goes live, note your URL — something like:

```
https://lighted-api.onrender.com
```

### Verify the API

Open these in a browser:

- `https://lighted-api.onrender.com/health` → `{"status":"ok","app":"LightEd","env":"production"}`
- `https://lighted-api.onrender.com/docs` → Swagger UI
- `https://lighted-api.onrender.com/courses` → `[]` ← **empty is expected right now**

If `/health` works but `/courses` 500s, your `DATABASE_URL` is wrong. Check the Render
logs: **Logs** tab → look for `psycopg` or `OperationalError`.

---

## Step 3 — Seed the database (do not skip)

1. In Render, open your `lighted-api` service.
2. Click the **Shell** tab (top right).
3. Run:

```bash
python -m app.db.seed
```

Expected output:

```
Seed complete.
  student@lighted.dev / password123
  teacher@lighted.dev / password123
  admin@lighted.dev   / password123
```

**Run it once only.** `users.email` is unique, so a second run fails with an
`IntegrityError` — harmless, but confusing. If you need to reset, truncate the tables
first (Neon SQL editor: `TRUNCATE users, courses, topics, lessons, quizzes, attempts,
enrollments, progress RESTART IDENTITY CASCADE;`) then re-run the seed.

4. Verify:

```
https://lighted-api.onrender.com/courses
```

Should now return **4 courses**. If it does, the backend is fully functional.

### Alternative if the Shell is unavailable

Temporarily set `APP_ENV=development` in Render's environment variables, save (this
triggers a restart), wait for the deploy, confirm `/courses` returns 4, then set
`APP_ENV=production` again and let it restart. The seed runs on boot only when the
`users` table is empty, so it is safe.

---

## Step 4 — Vercel (frontend)

1. Sign up at <https://vercel.com> with GitHub.
2. **Add New…** → **Project** → import your `lighted` repo.
3. Configure:

| Field | Value |
| --- | --- |
| Framework Preset | `Next.js` (auto-detected) |
| **Root Directory** | `apps/web` ← click **Edit** and set this |
| Build Command | leave default (`next build`) |
| Output Directory | leave default (`.next`) |
| Install Command | leave default (`npm install`) |

4. Expand **Environment Variables** and add:

| Key | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://lighted-api.onrender.com` |

No trailing slash. This value is **baked into the bundle at build time**, so if you
change it later you must redeploy.

5. **Deploy**. Takes ~2 minutes.

6. Your site is live at something like:

```
https://lighted.vercel.app
```

---

## Step 5 — Close the CORS loop (the step everyone forgets)

Right now the browser will block every API call, because the API only trusts
`localhost:3000`.

1. Copy your exact Vercel URL, e.g. `https://lighted.vercel.app`.
2. Render → `lighted-api` → **Environment** → edit `BACKEND_CORS_ORIGINS`:

```
https://lighted.vercel.app
```

3. **Save Changes** → Render redeploys automatically (~1 min).

Rules for this value:
- Exact origin: `https://`, the host, **no trailing slash**, no path.
- Multiple origins: comma-separated, no spaces.
- Include Vercel preview URLs only if you need them, e.g.
  `https://lighted.vercel.app,https://lighted-git-main-you.vercel.app`

---

## Step 6 — Smoke test (2 minutes)

Open your Vercel URL and check each box:

- [ ] Landing page loads, nav and hero render correctly
- [ ] **Log in** `student@lighted.dev` / `password123` → lands on `/dashboard`
- [ ] Dashboard shows **7/9 lessons, 78%** and real course bars
- [ ] **Courses** → 4 courses listed
- [ ] Open *Algebra Foundations* → curriculum accordion expands
- [ ] Open a lesson → content renders, "Mark as complete" works
- [ ] Take a quiz → submit → score screen with explanations appears
- [ ] **Progress** page shows the ring and course breakdown
- [ ] Log out → log in as `teacher@lighted.dev` → `/dashboard/teacher` with 5 students
- [ ] Log out → log in as `admin@lighted.dev` → `/dashboard/admin`, change a role
- [ ] Hard-refresh any page → still logged in (token persists)
- [ ] Browser console: no red errors

If all of those pass, you are live and functional.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Login returns `401` for the demo accounts | DB never seeded | Step 3 |
| `/courses` returns `[]` | Same | Step 3 |
| Console: `blocked by CORS policy` | `BACKEND_CORS_ORIGINS` wrong | Step 5 — exact origin, no trailing slash |
| Console: `Failed to fetch` / `ERR_CONNECTION_REFUSED` | `NEXT_PUBLIC_API_URL` still `localhost` | Fix in Vercel, then **redeploy** (it's build-time) |
| Requests go to `http://localhost:8000` on the live site | Env var added after the build | Vercel → Deployments → Redeploy |
| Render: `Application failed to respond` | Start command hardcoded port 8000 | Use `--port $PORT` |
| Render build fails on `psycopg` / `pydantic-core` | Wrong Python version | Set `PYTHON_VERSION=3.11.9`, clear build cache, redeploy |
| Render logs: `OperationalError` / `could not translate host` | Bad `DATABASE_URL` | Re-copy from Neon, keep `?sslmode=require` |
| First request takes ~50 seconds | Render free tier sleeps after 15 min idle | Expected. Upgrade or add a cron ping |
| `Mixed Content` errors | API on `http://` while site is `https://` | Always use `https://` for `NEXT_PUBLIC_API_URL` |
| Vercel build: `No such file or directory package.json` | Root Directory not set | Set it to `apps/web` |
| Data disappears after a while | Using Render's free Postgres (expires) | Use Neon (this guide) |

---

## After it's live

**Security, before sharing the link widely**

1. `JWT_SECRET_KEY` must be the random value, not `dev-only-change-me`.
2. Change the demo passwords, or delete the demo accounts, before real users exist.
3. Set `ACCESS_TOKEN_EXPIRE_MINUTES=60` for production (default is 1440 = 24h).

**Custom domains**

- Vercel → Project → Settings → Domains → add `app.yourdomain.com`, follow the DNS step.
- Then add that origin to `BACKEND_CORS_ORIGINS` on Render.
- Optional: `api.yourdomain.com` on Render → Settings → Custom Domain.

**When you're ready for AI**

The tutor endpoint is a labelled stub. `GUIDE.md` § 8 has the exact code to wire Gemini:
add `GEMINI_API_KEY` on Render, `pip install google-generativeai` (already in
requirements), replace the stub body in `apps/api/app/api/routes/ai.py`. Nothing else
changes — the frontend already calls `POST /ai/tutor`.

**Before real users**

- Add Alembic migrations instead of `create_all` (`GUIDE.md` § 3).
- Rate-limit `/auth/login` and `/ai/tutor`.
- Add refresh-token rotation.
