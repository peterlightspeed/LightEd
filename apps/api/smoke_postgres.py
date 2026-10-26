"""Production-path smoke test: runs the FastAPI app against a real PostgreSQL DB.

Usage:
    DATABASE_URL=postgresql://postgres@127.0.0.1:5433/lighted_test \
    APP_ENV=production python smoke_postgres.py

Mirrors what happens on Render: no auto-seed, tables already created, data seeded
explicitly. Exits non-zero on the first failure.
"""
import os
import sys

os.environ.setdefault("DATABASE_URL", "postgresql://postgres@127.0.0.1:5433/lighted_test")
os.environ.setdefault("APP_ENV", "production")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

import time
UNIQUE_EMAIL = f"prodtester+{int(time.time())}@example.com"

failures: list[str] = []
checks = 0


def check(label, condition, detail=""):
    global checks
    checks += 1
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        failures.append(label)


def login(client, email, password="password123"):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login {email} -> {r.status_code} {r.text}"
    return r.json()


with TestClient(app) as client:
    print("\n== meta ==")
    r = client.get("/health")
    check("health 200", r.status_code == 200, r.text)
    check("health env=production", r.json().get("env") == "production", r.text)
    check("root 200", client.get("/").status_code == 200)

    print("\n== anonymous ==")
    r = client.get("/courses")
    check("courses 200", r.status_code == 200, r.text)
    courses = r.json()
    check("4 courses seeded", len(courses) == 4, f"got {len(courses)}")
    check("course has lesson_count", all("lesson_count" in c for c in courses))
    check(
        "lesson counts 4/3/2/2",
        sorted(c["lesson_count"] for c in courses) == [2, 2, 3, 4],
        str([c["lesson_count"] for c in courses]),
    )
    check("anon not enrolled", all(c["enrolled"] is False for c in courses))

    print("\n== auth ==")
    check("bad password 401",
          client.post("/auth/login", json={"email": "student@lighted.dev", "password": "x"}).status_code == 401)
    check("unknown user 401",
          client.post("/auth/login", json={"email": "nobody@x.com", "password": "x"}).status_code == 401)

    student = login(client, "student@lighted.dev")
    teacher = login(client, "teacher@lighted.dev")
    admin = login(client, "admin@lighted.dev")
    check("student role", student["user"]["role"] == "student")
    check("teacher role", teacher["user"]["role"] == "teacher")
    check("admin role", admin["user"]["role"] == "admin")
    check("tokens present", all(t.get("access_token") for t in (student, teacher, admin)))

    sh = {"Authorization": f"Bearer {student['access_token']}"}
    th = {"Authorization": f"Bearer {teacher['access_token']}"}
    ah = {"Authorization": f"Bearer {admin['access_token']}"}

    check("no token on /auth/me -> 401", client.get("/auth/me").status_code == 401)
    check("bad token -> 401",
          client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401)
    r = client.get("/auth/me", headers=sh)
    check("/auth/me 200", r.status_code == 200, r.text)
    check("/auth/me email", r.json()["email"] == "student@lighted.dev")

    r = client.post("/auth/refresh", json={"refresh_token": student["refresh_token"]})
    check("refresh 200", r.status_code == 200, r.text)
    check("refresh returns access_token", bool(r.json().get("access_token")))

    check("forgot-password 200", client.post("/auth/forgot-password",
          json={"email": "student@lighted.dev"}).status_code == 200)
    check("google stub 501", client.post("/auth/google", json={"credential": "x"}).status_code == 501)

    print("\n== courses / lessons ==")
    r = client.get("/courses", headers=sh)
    check("courses with auth 200", r.status_code == 200)
    mine = [c for c in r.json() if c["enrolled"]]
    check("student enrolled in 3", len(mine) == 3, f"got {len(mine)}")

    cid = courses[0]["id"]
    r = client.get(f"/courses/{cid}", headers=sh)
    check("course detail 200", r.status_code == 200, r.text)
    detail = r.json()
    check("detail has topics", len(detail["topics"]) > 0)
    check("topics have lessons", all(len(t["lessons"]) > 0 for t in detail["topics"]))
    check("lesson has quiz_id field", "quiz_id" in detail["topics"][0]["lessons"][0])
    check("404 on missing course", client.get("/courses/99999", headers=sh).status_code == 404)

    lesson_id = detail["topics"][0]["lessons"][0]["id"]
    r = client.get(f"/lessons/{lesson_id}", headers=sh)
    check("lesson detail 200", r.status_code == 200, r.text)
    lesson = r.json()
    check("lesson has content", len(lesson.get("content", "")) > 50)
    check("lesson has course_title", bool(lesson.get("course_title")))

    # idempotent completion
    r1 = client.post(f"/lessons/{lesson_id}/complete", headers=sh)
    r2 = client.post(f"/lessons/{lesson_id}/complete", headers=sh)
    check("complete 200", r1.status_code == 200, r1.text)
    check("complete idempotent", r2.status_code == 200, r2.text)

    # idempotent enroll
    r1 = client.post(f"/courses/{cid}/enroll", headers=sh)
    r2 = client.post(f"/courses/{cid}/enroll", headers=sh)
    check("enroll 201", r1.status_code == 201, r1.text)
    check("enroll idempotent", r2.status_code == 201, r2.text)

    print("\n== quizzes ==")
    quiz_id = None
    for t in detail["topics"]:
        for l in t["lessons"]:
            if l.get("quiz_id"):
                quiz_id = client.get(f"/lessons/{l['id']}/quiz", headers=sh).json()["id"]
                break
        if quiz_id:
            break
    check("found a quiz", quiz_id is not None)

    r = client.get(f"/quizzes/{quiz_id}", headers=sh)
    check("quiz 200", r.status_code == 200, r.text)
    quiz = r.json()
    check("quiz has questions", len(quiz["questions"]) > 0)
    leaked = any("answer_index" in q for q in quiz["questions"])
    check("answer_index NOT leaked", not leaked)
    leaked_expl = any("explanation" in q for q in quiz["questions"])
    check("explanation NOT leaked", not leaked_expl)

    # all-correct submission
    n = len(quiz["questions"])
    r = client.post(f"/quizzes/{quiz_id}/attempts", headers=sh, json={"answers": [0] * n})
    check("attempt 201", r.status_code == 201, r.text)
    res = r.json()
    check("attempt graded", isinstance(res.get("score"), (int, float)))
    check("attempt has results", len(res["results"]) == n)
    check("results reveal correct_index", all("correct_index" in x for x in res["results"]))
    check("attempt persisted id", bool(res.get("id")))

    r = client.get("/attempts/me", headers=sh)
    check("my attempts 200", r.status_code == 200, r.text)

    print("\n== progress / dashboards ==")
    r = client.get("/progress/me", headers=sh)
    check("progress 200", r.status_code == 200, r.text)
    p = r.json()
    check("progress has courses", len(p["courses"]) > 0)
    check("progress overall_progress", isinstance(p["overall_progress"], (int, float)))
    check("progress recent_lessons", isinstance(p["recent_lessons"], list))

    r = client.get("/dashboard/student", headers=sh)
    check("student dashboard 200", r.status_code == 200, r.text)
    d = r.json()
    check("student stats present", "stats" in d)
    check("student stats lessons_total 9", d["stats"]["lessons_total"] == 9, str(d["stats"]))
    check("focus_areas list", isinstance(d.get("focus_areas"), list))
    check("recommendations list", isinstance(d.get("recommendations"), list))
    check("weekly_activity 7", len(d.get("weekly_activity", [])) == 7)

    r = client.get("/dashboard/teacher", headers=th)
    check("teacher dashboard 200", r.status_code == 200, r.text)
    t = r.json()
    check("teacher total_students 5", t["stats"]["total_students"] == 5, str(t["stats"]))
    check("teacher courses 4", t["stats"]["active_courses"] == 4, str(t["stats"]))
    check("teacher at_risk 2", t["stats"]["at_risk"] == 2, str(t["stats"]))
    check("teacher roster", len(t.get("students", [])) == 5)
    check("teacher at_risk count", t["stats"]["at_risk"] == 2, str(t["stats"]))
    check(
        "teacher roster at_risk statuses",
        len([s for s in t.get("students", []) if s.get("status") == "at_risk"]) == 2,
        str([(s.get("name"), s.get("status")) for s in t.get("students", [])]),
    )

    r = client.get("/dashboard/admin", headers=ah)
    check("admin dashboard 200", r.status_code == 200, r.text)
    a = r.json()
    check("admin users 7", a["stats"]["users"] == 7, str(a["stats"]))
    check("admin courses 4", a["stats"]["courses"] == 4, str(a["stats"]))
    check("admin attempts > 0", a["stats"]["attempts"] > 0, str(a["stats"]))

    print("\n== role enforcement ==")
    check("student -> teacher dash 403",
          client.get("/dashboard/teacher", headers=sh).status_code == 403)
    check("student -> admin dash 403",
          client.get("/dashboard/admin", headers=sh).status_code == 403)
    check("student -> admin users 403",
          client.get("/admin/users", headers=sh).status_code == 403)
    check("teacher -> admin dash 403",
          client.get("/dashboard/admin", headers=th).status_code == 403)
    check("anon -> student dash 401",
          client.get("/dashboard/student").status_code == 401)

    print("\n== admin mutations ==")
    r = client.get("/admin/users", headers=ah)
    check("admin users 200", r.status_code == 200, r.text)
    users = r.json()
    target = next(u for u in users if u["email"] == "priya@lighted.dev")
    r = client.patch(f"/admin/users/{target['id']}/role", headers=ah, json={"role": "teacher"})
    check("role patch 200", r.status_code == 200, r.text)
    check("role changed", r.json()["role"] == "teacher")
    # revert
    client.patch(f"/admin/users/{target['id']}/role", headers=ah, json={"role": "student"})

    r = client.patch(f"/admin/courses/{cid}/publish", headers=ah, json={"published": False})
    check("unpublish 200", r.status_code == 200, r.text)
    check("unpublished", r.json()["published"] is False)
    anon = client.get("/courses").json()
    check("unpublished hidden from anon", all(c["id"] != cid for c in anon))
    r = client.patch(f"/admin/courses/{cid}/publish", headers=ah, json={"published": True})
    check("republish 200", r.status_code == 200, r.text)

    print("\n== ai stub ==")
    r = client.post("/ai/tutor", headers=sh, json={"question": "What is a variable?", "lesson_id": lesson_id})
    check("ai tutor 200", r.status_code == 200, r.text)
    check("ai tutor provider=stub", r.json().get("provider") == "stub")
    check("ai tutor has answer", len(r.json().get("answer", "")) > 20)

    print("\n== CORS ==")
    r = client.options("/courses", headers={
        "Origin": "https://lighted.vercel.app",
        "Access-Control-Request-Method": "GET",
    })
    allow = r.headers.get("access-control-allow-origin")
    print(f"  CORS allow-origin for vercel origin: {allow!r} (None = not yet configured)")

    print("\n== registration (run last so user counts stay exact) ==")
    r = client.post("/auth/register", json={
        "full_name": "Prod Tester", "email": UNIQUE_EMAIL,
        "password": "testpass123", "role": "student"})
    check("register 201", r.status_code in (200, 201), r.text)
    check("register returns token", bool(r.json().get("access_token")))
    r = client.post("/auth/register", json={
        "full_name": "Dup", "email": UNIQUE_EMAIL,
        "password": "testpass123", "role": "student"})
    check("duplicate email rejected", r.status_code in (400, 409), f"{r.status_code}")


print("\n" + "=" * 60)
print(f"{checks - len(failures)}/{checks} checks passed")
if failures:
    print("FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("ALL CHECKS PASSED on PostgreSQL")
