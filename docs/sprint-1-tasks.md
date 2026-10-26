# Sprint 1 — Task List (copy these into GitHub Issues)

## Setup / Infra
- [ ] **chore(infra):** verify `docker compose up` brings up web + api + db
- [ ] **chore(ci):** confirm all three CI workflows pass on `develop`
- [ ] **chore(api):** run first Alembic migration and commit it

## Backend
- [ ] **feat(api):** JWT register + login endpoints (done in scaffold — verify)
- [ ] **feat(api):** refresh-token endpoint
- [ ] **feat(api):** RBAC dependency `require_roles` (done in scaffold — verify)
- [ ] **feat(api):** Course / Topic / Lesson CRUD (done — add update/delete)
- [ ] **feat(api):** Enrollment + attempt scoring (done — verify)
- [ ] **feat(api):** seed script with demo users + sample course
- [ ] **test(api):** cover auth + course flows

## AI
- [ ] **feat(ai):** wire `/ai/tutor` to `ai.tutor.answer_question`
- [ ] **feat(ai):** index seeded lessons into the retriever at startup
- [ ] **feat(ai):** connect quiz generation to `ai.quiz_generator`
- [ ] **test(ai):** weak-topic + revision-planner unit tests (done — extend)

## Frontend
- [ ] **feat(web):** login + register pages (done — connect to API)
- [ ] **feat(web):** protected route wrapper + redirect on 401
- [ ] **feat(web):** student dashboard with progress chart (done — use live data)
- [ ] **feat(web):** AI tutor chat component
- [ ] **feat(web):** course detail page + lesson viewer
- [ ] **feat(web):** quiz-taking UI with instant feedback

## Docs / Demo
- [ ] **docs:** fill README with real repo URL + screenshots
- [ ] **docs:** short demo script for the pitch
- [ ] **chore:** tag `v0.1.0-sprint1` at the end of the week

---

## Day 1 → Day 7 breakdown

| Day | Focus                    | Deliverable                                                        |
| --- | ------------------------ | ------------------------------------------------------------------ |
| 1   | Repo + env + Docker      | `docker compose up` works; CI green; team can clone & run          |
| 2   | Auth + RBAC              | Register/login working end-to-end; protected `/dashboard`          |
| 3   | Courses/Topics/Lessons   | Teacher can create a course; student can browse it                 |
| 4   | Enrollment + Quizzes     | Student enrolls, takes a quiz, gets a score                        |
| 5   | AI tutor MVP             | `/ai/tutor` returns grounded answers over seeded lessons           |
| 6   | Dashboards + charts      | Student progress chart + teacher class stats with live data        |
| 7   | Polish + demo            | Seed data, README, demo script, tag `v0.1.0-sprint1`               |
