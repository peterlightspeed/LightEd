# UPDATE_V5.md: review feedback + live classes

| Review point | Decision | What changed |
| --- | --- | --- |
| 1. Needs human images | Accepted | Original illustrated people (student, teacher + class, avatar group) on the landing hero, "who it's for" cards, final CTA and the login/register panel. No stock photos (licensing) and no fake testimonials. Real, consented photos can replace them: see `public/people/README.md`. |
| 2. Footer too generic | Accepted | Deep brand-navy footer (`navy-900`) with a gold/blue accent line, a clear "Questions? We're here to help" contact prompt, and tidy link columns. |
| 3. Section slider not useful | Accepted | Removed the in-page anchor links. Header is now just Log in / Get started. Sections reordered: Hero -> Who it's for (students + teachers merged) -> How it works -> What you get -> Sign up. |
| 4. "Good morning, Sam" | Accepted with a refinement | "Sam" was hard-coded in a **mock card on the landing page**, not the user's data. Removed. In the app the greeting is time-based ("Good morning/afternoon/evening"). Real accounts also see their **own** first name; the shared demo logins (`@lighted.dev`) show no name. |
| 5. Progress of people I don't know | Accepted | The landing "For teachers" mock listed named strangers with scores: removed. In the app a student only ever sees their own data (no leaderboard). A teacher sees only students enrolled in their own courses, by design and tested. |

## New: live classes
Teachers schedule a class (title, time, length, Meet/Zoom/Teams link). Enrolled students are notified, see **Live now** /
**Upcoming**, and tap **Join**. Dashboards show **Upcoming live classes**. New table `live_sessions` (created automatically).
See TEACHING_GUIDE.md for a 10-minute test script.

## Deploy
```bash
cd ~/lighted && git add -A
git commit -m "feat: live classes; landing redesign (people, dark footer, simpler nav); time-based greeting; remove fake people data"
git push origin main
```
