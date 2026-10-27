# UPDATE_V3.md — what's new and what to do

## 1. "There are no courses" — fixed (3 layers)
**Cause:** the server only seeded demo data when the *users* table was empty. If anyone signed up
first (or `SEED_ON_START` wasn't set), the catalogue stayed empty forever.

**Fix:**
1. The server now seeds whenever there are **no courses** (not "no users"). The seed is idempotent and re-uses
   existing demo users. Result: 4 starter courses (Algebra, Biology, History, Coding) with lessons + quizzes.
2. **Teachers can now build courses themselves** in the app (no code, no Swagger):
   `Courses → + New course → add topics → + Lesson → Quiz → Generate draft → edit → Approve & publish`.
3. On Render set `SEED_ON_START=true` once (see FIX_BACKEND.md). After the redeploy, open the site: courses appear.

## 2. Teachers can see their students
- **Students** tab (teacher/admin): everyone enrolled in *your* courses, sorted so students needing help come first.
- Tap a student → progress per course, topic accuracy (weak topics < 60%), recent quizzes, and a plain-English
  **risk reason** ("Average quiz score is 48%", "No activity for over 14 days").
- Teachers only ever see students in their own courses (admins see all). Covered by tests.
- Students appear when they enrol (Courses → Enrol). Demo: log in as `teacher@lighted.dev`.

## 3. PWA — install alert
- LightEd is installable (manifest + service worker + icons + offline page).
- A dismissible **"Install LightEd"** alert appears after a few seconds: Android/desktop Chrome get a real
  *Install app* button; iPhone/iPad Safari get "Share → Add to Home Screen" steps. Never shown if already installed;
  "Not now" hides it for 7 days.
- Test it: open the **deployed https site** (installs need HTTPS; localhost works too) in Chrome → wait ~6 s.
  DevTools → Application → Manifest shows installability.
- After each deploy bump `VERSION` in `apps/web/public/sw.js` if you change cached assets.

## 4. Mobile UI fixes
Bottom tab bar (Home / Courses / Tutor / Planner / Progress; teachers: Home / Courses / Students / Tutor) ·
2-column stat grids · tables become cards on phones · 44px tap targets · 16px inputs (no iOS zoom) ·
notch/safe-area support · no sideways scrolling (grid overflow fixed) · tutor chat fits the screen · teachers no
longer see "Enrol for free".

## 5. Features added from the PDF report
| PDF requirement | Status |
| --- | --- |
| FR-04 teachers create/edit courses, topics, lessons | ✅ in-app |
| FR-10/11 AI quiz generation + teacher review/edit/publish | ✅ (Gemini if key set, else offline generator) |
| FR-08/09 AI tutor, grounded in course material **with sources** | ✅ new `/tutor` page |
| FR-14 weak-topic detection (<60%) | ✅ student + teacher views |
| FR-17 revision planner (exam date + daily minutes) | ✅ new `/planner` page |
| FR-19/21 at-risk list + simple risk score | ✅ rule-based, with reasons |
| FR-24 audit logs (logins, failed logins, role changes, quiz publish) | ✅ Admin dashboard → Audit log |
| FR-22 notifications, FR-25 dark mode, FR-05 PDF upload, class join codes | ⏳ not yet (see todo.md) |

## 6. Optional: real AI (Gemini)
Works without any key (offline mode). For real LLM answers/quizzes add on Render: `GEMINI_API_KEY` (free key at
aistudio.google.com). Optional `GEMINI_MODEL` (default `gemini-1.5-flash`). Answers stay grounded in course text.

## 7. Deploy
```bash
cd ~/lighted && git add -A
git commit -m "feat: teacher course authoring + student roster/risk, PWA install, mobile UI overhaul, AI tutor, planner, audit log"
git push origin main
```
Render: add `SEED_ON_START=true` (and optional `GEMINI_API_KEY`), redeploy. Vercel redeploys automatically.
New DB table `audit_logs` is created automatically on startup (no existing tables were changed).
