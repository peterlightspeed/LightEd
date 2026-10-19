# Roadmap

## Sprint 1 — Foundations (Week 1)

**Goal:** a working skeleton — auth, courses, AI tutor MVP, one dashboard.

- [ ] Repo scaffold, CI green, Docker compose up
- [ ] JWT register/login + RBAC dependencies
- [ ] Course / Topic / Lesson CRUD endpoints
- [ ] Enrollment + quiz attempt flow (stubbed quiz gen)
- [ ] AI tutor endpoint wired to `ai.tutor` (RAG over seeded lessons)
- [ ] Student dashboard with progress chart
- [ ] Seed script with demo users + a sample course
- [ ] Docs + `.env.example` complete

## Sprint 2 — AI Depth (Week 2)

- [ ] Real quiz generation via Gemini (`ai.quiz_generator`)
- [ ] Embeddings-based topic recommendations
- [ ] Weak-topic detection surfaced in the student dashboard
- [ ] Performance prediction endpoint
- [ ] Revision planner UI
- [ ] FAISS-backed retriever (replace in-memory)

## Sprint 3 — Teacher & Analytics (Week 3)

- [ ] Teacher dashboard: class analytics, at-risk students
- [ ] Course authoring UI (topics, lessons, quizzes)
- [ ] Learning analytics charts (Chart.js)
- [ ] Admin user management

## Sprint 4 — Polish & Deploy (Week 4)

- [ ] E2E tests (Playwright)
- [ ] Vercel (web) + Render (api, ai) deployment
- [ ] Redis caching for hot endpoints
- [ ] Accessibility + responsive polish
- [ ] Demo script + pitch deck
