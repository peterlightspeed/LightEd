# UPDATE_V4.md

## What's new
| Area | Change |
| --- | --- |
| **Courses** | 10 starter courses (6 new: English, Physics, Chemistry, Digital Skills, Financial Literacy, Entrepreneurship). They are **added automatically on startup, even on a database that already has courses** (matched by title, never duplicated). |
| **PWA prompt** | Fixed the nagging. It now appears **once**, only inside the signed-in app, after ~25 s, then stays quiet for 14 days (30 days after "Not now"/Install). Never on landing/login. |
| **Layout** | Cards now have proper padding (the old `.card` had none, causing the cramped/overlapping look). Course colour headers were missing because Tailwind didn't scan `src/lib` — fixed. Tables become cards on phones. |
| **Dark mode** | Toggle (moon/sun) in the header; remembers your choice and follows the device setting. |
| **Notifications** | Bell with unread count: new enrolment / class-code join (teacher), new quiz (students), low score <50% (teacher). |
| **Class codes** | Teachers see a 6-char code per course (Manage this course). Students: Courses → "Join with a class code". |
| **Materials** | Teachers can import text from a PDF into a lesson and attach resource links; students see them under "Go deeper". |
| **Password reset** | Real flow: email link → `/reset-password` (single-use, 30-minute token, stored hashed). |
| **Rate limiting** | Login 10/min, register 8/10 min, reset 5/5 min, tutor 30/min (per IP, in-memory). |
| **Alembic** | Baseline migration `0001`. For a DB created by the app already run once: `alembic stamp head`. |
| **ML prototype** | `ai/lighted_ai/train_risk_model.py` (Random Forest on SYNTHETIC data; the live API still uses the explainable rule-based score). |

## To enable password-reset emails (optional)
On Render add: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER=lightedsupport@gmail.com`,
`SMTP_PASSWORD=<Google App Password>` (Google Account → Security → 2-Step Verification → App passwords),
and `FRONTEND_URL=https://light-ed.vercel.app`. Without SMTP the reset link is written to the server log.

## Deploy
```bash
cd ~/lighted && git add -A
git commit -m "feat: 10 starter courses, calmer PWA prompt, dark mode, notifications, class codes, PDF import, password reset, rate limiting; fix card padding + Tailwind scan"
git push origin main
```
Render redeploys; new tables (`notifications`, `course_join_codes`, `lesson_resources`, `password_resets`, `audit_logs`) are created automatically.
