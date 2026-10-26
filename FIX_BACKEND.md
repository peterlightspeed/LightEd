# FIX_BACKEND.md — fixing the two backend problems

You hit two different problems. Fix **A** to run the API on your Chromebook (Debian "penguin"),
and **B** to make the deployed site (Vercel → Render) stop failing with a CORS error.

---

## A. Local: `error: externally-managed-environment` / `No module named 'sqlalchemy'`

**Cause.** Debian/Python 3.13 refuses `pip install` into the system Python (PEP 668). Because the
install failed, nothing was installed, so `seed.py` could not import `sqlalchemy`.
There was also no `.venv` yet, so `source .venv/bin/activate` failed.

**Fix — create a virtual environment (one time):**

```bash
sudo apt update && sudo apt install -y python3-venv python3-full

cd ~/lighted/apps/api
python3 -m venv .venv            # creates the .venv folder
source .venv/bin/activate        # your prompt now starts with (.venv)
pip install --upgrade pip
pip install -r requirements.txt  # works on Python 3.13 now (old pins were removed)
```

**Every new terminal** you must re-activate it: `cd ~/lighted/apps/api && source .venv/bin/activate`.

**Run locally with zero database setup (SQLite):**

```bash
# IMPORTANT: if you copied .env.example to .env, comment out the DATABASE_URL line.
# It points at a local Postgres that you probably don't have running -> connection refused.
# With DATABASE_URL unset, the API uses a local SQLite file automatically.

python -m app.db.seed                       # creates tables + demo users/courses
uvicorn app.main:app --reload --port 8000   # http://localhost:8000/docs
```

(Don't `export APP_ENV=production` locally — it is only needed on the server. In the default
`development` mode the API auto-creates tables and auto-seeds when the DB is empty.)

Demo logins (password `password123`): `student@lighted.dev`, `teacher@lighted.dev`, `admin@lighted.dev`.

Run the tests any time: `pytest -q` (expect `9 passed`).

---

## B. Deployed: `blocked by CORS policy ... No 'Access-Control-Allow-Origin' header`

The error appeared on `POST https://lighted-api.onrender.com/auth/register` from
`https://light-ed.vercel.app`. **It is a symptom, not always a real CORS bug.** The browser shows
this message whenever the response has no CORS header, which happens in four situations:

| # | Real cause | Fixed in this version by |
|---|---|---|
| 1 | `BACKEND_CORS_ORIGINS` on Render doesn't exactly equal your Vercel URL (unset, a trailing `/`, `http` vs `https`, a typo) | New `FRONTEND_URL` variable, trailing slashes/quotes auto-stripped, and `*.vercel.app` is allowed by default |
| 2 | Render **free tier was asleep** — the proxy answers 502 (no CORS header) while the app boots (30–60 s) | Frontend warms the API on page load, retries network failures, and shows a "waking up the server" message |
| 3 | The API **crashed** (500) — unhandled errors skip CORS | Errors are now caught *inside* the CORS layer so you see the real error |
| 4 | Build/boot failure (e.g. pinned packages can't build on Python 3.13) | Requirements updated + Python pinned to 3.11.9 |

### Step-by-step on Render (do all of these)

1. **Push this version to GitHub** (commands at the bottom) so Render redeploys.
2. Render → your `lighted-api` service → **Environment**, set exactly:

   | Key | Value |
   | --- | --- |
   | `PYTHON_VERSION` | `3.11.9` |
   | `APP_ENV` | `production` |
   | `DATABASE_URL` | your Neon string, pasted exactly as given (ends with `?sslmode=require`) |
   | `JWT_SECRET_KEY` | long random string (`python -c "import secrets;print(secrets.token_urlsafe(48))"`) |
   | `FRONTEND_URL` | `https://light-ed.vercel.app` ← **no trailing slash** |
   | `SEED_ON_START` | `true` (creates demo users/courses once, only if the DB is empty — Render free has no shell) |
   | `GOOGLE_CLIENT_ID` | *(later — see GOOGLE_AUTH.md)* |

   Build command: `pip install -r requirements.txt` · Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` · Root directory: `apps/api`.
3. **Manual Deploy → Deploy latest commit.** Watch the **Logs** until you see `Application startup complete`.
4. Open `https://lighted-api.onrender.com/health` in a browser. You should see JSON.
   **Check that `cors_origins` contains `https://light-ed.vercel.app`.** If not, the env var is wrong.
5. Test the exact browser preflight from your terminal:

   ```bash
   curl -i -X OPTIONS https://lighted-api.onrender.com/auth/register \
     -H "Origin: https://light-ed.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: content-type"
   ```
   You must see `HTTP/2 200` and `access-control-allow-origin: https://light-ed.vercel.app`.
6. **Vercel** → Project → Settings → Environment Variables: `NEXT_PUBLIC_API_URL` = `https://lighted-api.onrender.com`
   (no trailing slash). **Then Redeploy** — `NEXT_PUBLIC_*` values are baked in at *build* time, so
   changing it without redeploying does nothing.
7. Hard-refresh the site (Ctrl+Shift+R) and register again. The first request after idle can take up
   to a minute on Render's free plan; the form now tells you it's waking the server.

### Still failing? Read the status code

Browser → DevTools → **Network** → click the failed request:

| You see | Meaning | Do this |
| --- | --- | --- |
| `(failed) net::ERR_FAILED`, no status | Server asleep / down / wrong URL | Open `/health` in a tab, wait for it, retry; check the URL in Vercel env |
| `502` / `503` | Render still booting or crashed | Render → Logs |
| `500` | Code/DB error (now shows CORS headers + real message) | Render → Logs (look for the traceback) |
| `400 Email already registered` | Works! Account exists | Log in instead |
| `401` on login | Empty DB (not seeded) or wrong password | Set `SEED_ON_START=true`, redeploy, or register a new account |

> **Console noise you can ignore:** `[ats-applied]`, `[jobright] runtime activation…`, and
> `Forced reflow` come from browser extensions / the browser, not from LightEd.
> The `favicon.ico 404` is fixed (the logo is now the site icon).

---

## Git: push this fix

```bash
cd ~/lighted
git add -A
git commit -m "fix(api): resolve production CORS, add Google auth, brand logo, product tour"
git push origin main
```
Render and Vercel both redeploy automatically on push (Render: or press **Manual Deploy**).
