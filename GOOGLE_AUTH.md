# GOOGLE_AUTH.md — turn on "Continue with Google"

Code is **already wired** (backend `POST /auth/google`, frontend button on Login + Register).
It stays hidden until you add a Google client ID. You only need to set **one** env var, on the **backend**.

## 1. Create the client ID (≈5 minutes, free)

1. <https://console.cloud.google.com> → create/select a project (e.g. `LightEd`).
2. **APIs & Services → OAuth consent screen**: choose **External**, app name `LightEd`,
   support email `lightedsupport@gmail.com`, developer contact email → Save.
   Scopes: the defaults (`email`, `profile`, `openid`) are enough.
3. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   - Application type: **Web application**
   - **Authorized JavaScript origins** (add each, no trailing slash, no path):
     - `https://light-ed.vercel.app`
     - `http://localhost:3000`
   - *Authorized redirect URIs:* leave **empty** (the Google button uses the token flow, not redirects).
4. Copy the **Client ID** (`123456-abc.apps.googleusercontent.com`). You do not need the client secret.

## 2. Configure

| Where | Key | Value |
| --- | --- | --- |
| Render (backend) | `GOOGLE_CLIENT_ID` | the client ID |
| Local `apps/api/.env` | `GOOGLE_CLIENT_ID` | the client ID |

Redeploy Render. Check `https://lighted-api.onrender.com/health` → `"google_enabled": true`.
(The frontend discovers the client ID from `GET /auth/providers`, so Vercel needs **no** change.
Optional fallback: `NEXT_PUBLIC_GOOGLE_CLIENT_ID` on Vercel.)

## 3. Publish the consent screen
While the app is in **Testing**, only the "Test users" you list can sign in. For everyone:
**OAuth consent screen → Publish app** (basic scopes need no Google review).

## How it behaves
- New Google user → account created (role = what they chose on Register, otherwise `student`; never admin).
- Existing email → they are signed into the existing account (Google verified the email).
- Google-created accounts have no password; trying password login gives a clear message.

## Troubleshooting
| Symptom | Fix |
| --- | --- |
| No Google button | `/auth/providers` returns `null` → `GOOGLE_CLIENT_ID` not set / not redeployed |
| Popup says `origin_mismatch` / "Not a valid origin" | Add the exact site origin in step 1.3 (changes take a few minutes) |
| `Google sign-in was issued for a different app` | The `GOOGLE_CLIENT_ID` on Render ≠ the one the site used |
| 503 "Could not reach Google" | Render can't reach `oauth2.googleapis.com`; retry |
