# API Reference (v0.1)

Base URL: `http://localhost:8000` (dev) — interactive docs at `/docs`.

## Auth

| Method | Path             | Auth | Description              |
| ------ | ---------------- | ---- | ------------------------ |
| POST   | `/auth/register` | —    | Create account           |
| POST   | `/auth/login`    | —    | Get access + refresh JWT |

## Courses / Topics / Lessons

| Method | Path                        | Auth        | Description            |
| ------ | --------------------------- | ----------- | ---------------------- |
| GET    | `/courses`                  | —           | List courses           |
| POST   | `/courses`                  | teacher/admin | Create course        |
| GET    | `/courses/{id}`             | —           | Get course             |
| GET    | `/courses/{id}/topics`      | —           | List topics            |
| POST   | `/topics`                   | teacher/admin | Create topic         |
| GET    | `/topics/{id}/lessons`      | —           | List lessons           |
| POST   | `/lessons`                  | teacher/admin | Create lesson        |

## Enrollments

| Method | Path                 | Auth    | Description            |
| ------ | -------------------- | ------- | ---------------------- |
| POST   | `/enrollments`       | student | Enroll in a course     |
| GET    | `/enrollments/me`    | student | My enrollments         |

## Quizzes & Attempts

| Method | Path             | Auth          | Description              |
| ------ | ---------------- | ------------- | ------------------------ |
| POST   | `/quizzes`       | teacher/admin | Generate quiz for lesson |
| GET    | `/quizzes/{id}`  | —             | Get quiz                 |
| POST   | `/attempts`      | student       | Submit answers, get score|
| GET    | `/attempts/me`   | student       | My attempt history       |

## Dashboards

| Method | Path                 | Auth          | Description            |
| ------ | -------------------- | ------------- | ---------------------- |
| GET    | `/dashboard/student` | student       | Student summary        |
| GET    | `/dashboard/teacher` | teacher/admin | Class analytics        |

## AI

| Method | Path          | Auth    | Description                          |
| ------ | ------------- | ------- | ------------------------------------ |
| POST   | `/ai/tutor`   | student | Ask the AI tutor (RAG-grounded)      |

## Meta

| Method | Path       | Description     |
| ------ | ---------- | --------------- |
| GET    | `/health`  | Health check    |
| GET    | `/`        | API info        |

### Example: login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"secret123"}'
```

### Example: authenticated call

```bash
curl http://localhost:8000/dashboard/student \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
