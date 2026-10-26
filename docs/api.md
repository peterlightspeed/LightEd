# LightEd API Reference

Base URL: `http://localhost:8000` (dev) · interactive Swagger at `/docs` · OpenAPI JSON at `/openapi.json`.

All request and response bodies are JSON. Protected routes expect:

```
Authorization: Bearer <access_token>
```

Errors use FastAPI's standard shape:

```json
{ "detail": "Human-readable message" }
```

with `401` for missing/expired tokens, `403` for wrong role, `404` for missing resources,
and `409` for conflicts.

---

## Auth

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | — | Create a student or teacher account |
| POST | `/auth/login` | — | Exchange email + password for tokens |
| POST | `/auth/refresh` | — | Exchange a refresh token for a new access token |
| GET | `/auth/me` | user | Current user profile |
| POST | `/auth/forgot-password` | — | Always returns 200 (no email is sent) |
| POST | `/auth/google` | — | **Not implemented** — returns 501 |

### `POST /auth/register`

```json
{
  "full_name": "Sam Rivera",
  "email": "sam@example.com",
  "password": "at-least-6-chars",
  "role": "student"
}
```

`role` accepts `student` or `teacher`. Admin accounts cannot be self-registered.

**201**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 4,
    "full_name": "Sam Rivera",
    "email": "sam@example.com",
    "role": "student",
    "avatar_url": null,
    "created_at": "2026-10-26T13:00:00Z"
  }
}
```

### `POST /auth/login`

```json
{ "email": "student@lighted.dev", "password": "password123" }
```

Returns the same `TokenResponse` shape as register. `401` on bad credentials.

### `GET /auth/me`

Returns the `User` object only (no tokens). Used by the frontend on boot to validate a
stored token.

---

## Courses

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/courses` | optional | Catalogue. Anonymous callers see published courses only |
| GET | `/courses/mine` | user | Courses the caller owns or is enrolled in |
| POST | `/courses` | teacher/admin | Create a course |
| GET | `/courses/{id}` | optional | Detail + full curriculum + enrollment state |
| POST | `/courses/{id}/enroll` | user | Idempotent enrollment |
| GET | `/courses/{id}/topics` | optional | Flat list of topics |
| POST | `/courses/{id}/topics` | teacher/admin | Create a topic |
| GET | `/courses/{id}/lessons` | optional | Flat list of lesson summaries |
| POST | `/courses/{id}/lessons` | teacher/admin | Create a lesson |
| GET | `/enrollments/me` | user | The caller's enrollments |

### `GET /courses` → `Course[]`

```json
[
  {
    "id": 1,
    "title": "Algebra Foundations",
    "description": "Build confidence with variables, equations and graphs.",
    "subject": "Mathematics",
    "level": "Beginner",
    "accent": "blue",
    "published": true,
    "lesson_count": 4,
    "topic_count": 2,
    "owner_name": "Tara Mensah",
    "enrolled": true,
    "lessons_completed": 3
  }
]
```

`enrolled` and `lessons_completed` are only meaningful when the request carries a token;
they are `false` / `0` for anonymous callers.

### `GET /courses/{id}` → `CourseDetail`

Adds `topics`, each containing `lessons`:

```json
{
  "id": 1,
  "title": "Algebra Foundations",
  "...": "same fields as Course",
  "topics": [
    {
      "id": 1,
      "title": "Variables & Expressions",
      "position": 1,
      "lessons": [
        {
          "id": 1,
          "title": "What is a variable?",
          "summary": "Letters that stand in for numbers.",
          "duration_minutes": 12,
          "position": 1,
          "completed": true,
          "has_quiz": true
        }
      ]
    }
  ]
}
```

### `POST /courses/{id}/enroll`

No body. Returns `EnrollmentOut`. Calling it twice is safe — the unique constraint on
`(user_id, course_id)` means the second call is a no-op, not an error.

---

## Lessons

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/lessons/{id}` | user | Full lesson content |
| POST | `/lessons/{id}/complete` | user | Idempotent completion |

### `GET /lessons/{id}` → `LessonDetail`

```json
{
  "id": 1,
  "title": "What is a variable?",
  "summary": "Letters that stand in for numbers.",
  "content": "A variable is a letter...\n\n**Key idea**\n\nIt stands for an unknown.",
  "duration_minutes": 12,
  "position": 1,
  "course_id": 1,
  "course_title": "Algebra Foundations",
  "topic_id": 1,
  "topic_title": "Variables & Expressions",
  "completed": true,
  "quiz_id": 1,
  "prev_lesson_id": null,
  "next_lesson_id": 2
}
```

`content` is plain text. Paragraphs are separated by blank lines; `**bold**` marks
headings and emphasis. The frontend renders this without a markdown library.

---

## Quizzes

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/quizzes/lesson/{lesson_id}` | user | Quiz for a lesson (404 if none) |
| GET | `/quizzes/{id}` | user | Quiz **without** answer keys |
| POST | `/quizzes/{id}/attempts` | user | Submit answers, receive graded result |
| GET | `/quizzes/attempts/me` | user | The caller's attempt history |

### `GET /quizzes/{id}` → `Quiz`

```json
{
  "id": 1,
  "lesson_id": 1,
  "lesson_title": "What is a variable?",
  "pass_mark": 70,
  "questions": [
    {
      "id": 1,
      "prompt": "Which of these is a variable?",
      "options": ["3", "x", "7 + 2", "="]
    }
  ]
}
```

> `answer_index` and `explanation` are **deliberately omitted** here. They are only
> revealed in the attempt result, after grading.

### `POST /quizzes/{id}/attempts`

```json
{ "answers": [1, 0, 2, 3] }
```

One entry per question, in order. Use `-1` for unanswered.

**200** → `AttemptResult`

```json
{
  "attempt_id": 14,
  "quiz_id": 1,
  "score": 75,
  "correct": 3,
  "total": 4,
  "passed": true,
  "results": [
    {
      "question_id": 1,
      "prompt": "Which of these is a variable?",
      "options": ["3", "x", "7 + 2", "="],
      "selected_index": 1,
      "answer_index": 1,
      "correct": true,
      "explanation": "x is a letter standing in for an unknown value."
    }
  ]
}
```

Grading happens entirely server-side. The attempt is persisted and immediately reflected
in `/progress/me` and the dashboards.

---

## Progress

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/progress/me` | user | Full progress payload |

```json
{
  "lessons_completed": 7,
  "lessons_total": 9,
  "overall_progress": 78,
  "avg_score": 82,
  "streak_days": 4,
  "courses": [
    {
      "course_id": 1,
      "title": "Algebra Foundations",
      "accent": "blue",
      "lessons_completed": 3,
      "lesson_count": 4,
      "progress": 75,
      "avg_score": 88
    }
  ],
  "recent_lessons": [
    {
      "lesson_id": 5,
      "title": "Cell structures",
      "course_title": "Biology: Cells to Systems",
      "completed_at": "2026-10-25T09:14:00Z"
    }
  ]
}
```

---

## Dashboards

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/dashboard/student` | student | Student home payload |
| GET | `/dashboard/teacher` | teacher/admin | Class analytics |
| GET | `/dashboard/admin` | admin | Platform stats |

### `GET /dashboard/student`

```json
{
  "stats": {
    "courses_enrolled": 3,
    "lessons_completed": 7,
    "lessons_total": 9,
    "avg_score": 82,
    "streak_days": 4
  },
  "continue_learning": {
    "course_id": 2,
    "course_title": "Biology: Cells to Systems",
    "lesson_id": 5,
    "lesson_title": "Cell structures",
    "progress": 67
  },
  "focus_areas": [
    { "course_id": 3, "title": "World History: Modern Era", "mastery": 61, "status": "developing" }
  ],
  "recommendations": [
    { "course_id": 4, "title": "Intro to Programming", "reason": "Not started yet", "accent": "violet" }
  ],
  "weekly_activity": [1, 0, 2, 1, 3, 0, 1],
  "recent_quizzes": [
    { "quiz_id": 2, "lesson_title": "Cell structures", "score": 75, "taken_at": "2026-10-25T09:20:00Z" }
  ]
}
```

### `GET /dashboard/teacher`

```json
{
  "stats": {
    "total_students": 5,
    "active_courses": 4,
    "class_average": 69,
    "at_risk": 2
  },
  "courses": [
    { "course_id": 1, "title": "Algebra Foundations", "students": 4, "avg_progress": 72, "avg_score": 78 }
  ],
  "at_risk_students": [
    { "user_id": 5, "full_name": "Amina Yusuf", "email": "amina@lighted.dev", "avg_score": 48, "lessons_completed": 3 }
  ],
  "students": [
    {
      "user_id": 3,
      "full_name": "Sam Rivera",
      "email": "student@lighted.dev",
      "avg_score": 82,
      "lessons_completed": 7,
      "status": "on_track"
    }
  ]
}
```

`status` is `on_track` (≥70), `developing` (50–69) or `at_risk` (<50).

### `GET /dashboard/admin`

```json
{
  "stats": { "users": 7, "students": 5, "teachers": 1, "courses": 4, "attempts": 12 },
  "users": [
    { "id": 3, "full_name": "Sam Rivera", "email": "student@lighted.dev", "role": "student", "created_at": "..." }
  ],
  "courses": [
    { "id": 1, "title": "Algebra Foundations", "published": true, "lesson_count": 4, "students": 4 }
  ]
}
```

---

## Admin

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/admin/users` | admin | All users |
| PATCH | `/admin/users/{id}/role` | admin | Change a user's role |
| PATCH | `/admin/courses/{id}/publish` | admin | Publish / unpublish |

```json
PATCH /admin/users/3/role
{ "role": "teacher" }

PATCH /admin/courses/2/publish
{ "published": false }
```

Both return the updated object.

---

## AI

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/ai/tutor` | user | **Stub** — returns a canned reply |

```json
POST /ai/tutor
{ "message": "Explain variables", "lesson_id": 1 }

→ 200
{ "reply": "I'm a placeholder tutor...", "stub": true }
```

See `GUIDE.md § 8` for wiring Gemini.

---

## Health

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/health` | — | Liveness probe |

```json
{ "status": "ok", "app": "LightEd", "env": "development" }
```
