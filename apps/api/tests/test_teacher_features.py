"""Teacher roster/risk, quiz authoring, planner, tutor, audit and the seed-gating fix."""
from datetime import date, timedelta


def _signup(client, email, role="student", name=None):
    r = client.post("/auth/register", json={"full_name": name or email.split("@")[0].title(), "email": email,
                                            "password": "secret123", "role": role})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _build_course(client, t):
    c = client.post("/courses", json={"title": "Physics 101", "description": "d", "subject": "Science"}, headers=t).json()
    tp = client.post(f"/courses/{c['id']}/topics", json={"title": "Motion", "order_index": 1}, headers=t).json()
    content = ("Velocity describes how quickly an object changes position over time. "
               "Acceleration describes how quickly the velocity itself changes over time.\n\n"
               "Newton showed that force equals mass multiplied by acceleration for every object.")
    l = client.post("/lessons", json={"topic_id": tp["id"], "title": "Velocity", "summary": "s", "content": content,
                                      "duration_minutes": 10, "order_index": 1}, headers=t).json()
    return c, l


def test_seed_runs_even_if_users_already_exist(client):
    """Regression: an early sign-up used to block seeding -> empty course list."""
    from app.db.seed import seed
    from app.db.session import SessionLocal
    from app.models.course import Course
    from sqlalchemy import select

    _signup(client, "early-bird@example.com")
    db = SessionLocal()
    try:
        if db.scalar(select(Course).limit(1)) is None:
            seed()
        assert db.scalar(select(Course).limit(1)) is not None
    finally:
        db.close()
    assert len(client.get("/courses").json()) >= 1


def test_quiz_authoring_review_publish_and_grading(client):
    t = _signup(client, "auth-teacher@example.com", "teacher")
    s = _signup(client, "auth-student@example.com")
    c, l = _build_course(client, t)

    draft = client.post(f"/lessons/{l['id']}/quiz/generate", json={"num_questions": 3, "difficulty": "easy"}, headers=t)
    assert draft.status_code == 200 and draft.json()["questions"]
    # students cannot author
    assert client.post(f"/lessons/{l['id']}/quiz/generate", json={}, headers=s).status_code == 403
    # invalid edit is rejected
    bad = client.put(f"/lessons/{l['id']}/quiz", json={"questions": [{"prompt": "x", "options": ["a"], "answer_index": 0}]}, headers=t)
    assert bad.status_code == 422
    # approve & publish
    ok = client.put(f"/lessons/{l['id']}/quiz", json={"questions": draft.json()["questions"]}, headers=t)
    assert ok.status_code == 200
    # students get the quiz WITHOUT answers
    q = client.get(f"/lessons/{l['id']}/quiz", headers=s).json()
    assert "answer_index" not in q["questions"][0]
    # teacher can fetch it with answers for editing
    assert "answer_index" in client.get(f"/lessons/{l['id']}/quiz/edit", headers=t).json()["questions"][0]


def test_teachers_cannot_edit_other_teachers_courses(client):
    t1 = _signup(client, "own-a@example.com", "teacher")
    t2 = _signup(client, "own-b@example.com", "teacher")
    c, l = _build_course(client, t1)
    assert client.post(f"/courses/{c['id']}/topics", json={"title": "Hack", "order_index": 2}, headers=t2).status_code == 403
    assert client.put(f"/lessons/{l['id']}/quiz", json={"questions": []}, headers=t2).status_code in (403, 422)


def test_teacher_sees_only_own_students_with_risk(client):
    t1 = _signup(client, "roster-a@example.com", "teacher")
    t2 = _signup(client, "roster-b@example.com", "teacher")
    mine = _signup(client, "mine-student@example.com", name="Mine Student")
    other = _signup(client, "other-student@example.com", name="Other Student")
    c1, l1 = _build_course(client, t1)
    c2, _ = _build_course(client, t2)
    client.post(f"/courses/{c1['id']}/enroll", headers=mine)
    client.post(f"/courses/{c2['id']}/enroll", headers=other)

    # give 'mine' a failing attempt so risk is flagged
    quiz = client.put(f"/lessons/{l1['id']}/quiz", json={"questions": [
        {"prompt": "Q1", "options": ["a", "b"], "answer_index": 0},
        {"prompt": "Q2", "options": ["a", "b"], "answer_index": 0}]}, headers=t1).json()
    client.post(f"/quizzes/{quiz['id']}/attempts", json={"answers": [1, 1]}, headers=mine)

    roster = client.get("/teacher/students", headers=t1).json()
    names = [s["name"] for s in roster["students"]]
    assert names == ["Mine Student"]
    assert roster["students"][0]["risk"]["band"] in ("medium", "high")
    assert roster["students"][0]["risk"]["factors"]

    detail = client.get(f"/teacher/students/{roster['students'][0]['id']}", headers=t1).json()
    assert detail["recent_attempts"] and detail["course_progress"]
    # cannot peek at another teacher's student
    other_id = client.get("/teacher/students", headers=t2).json()["students"][0]["id"]
    assert client.get(f"/teacher/students/{other_id}", headers=t1).status_code == 404
    # students are forbidden
    assert client.get("/teacher/students", headers=mine).status_code == 403
    # dashboard is scoped too
    assert client.get("/dashboard/teacher", headers=t1).json()["stats"]["total_students"] == 1


def test_tutor_is_grounded_with_sources(client):
    t = _signup(client, "tutor-teacher@example.com", "teacher")
    s = _signup(client, "tutor-student@example.com")
    c, _ = _build_course(client, t)
    client.post(f"/courses/{c['id']}/enroll", headers=s)
    r = client.post("/ai/tutor", json={"question": "What is acceleration?"}, headers=s).json()
    assert "velocity" in r["answer"].lower() and r["sources"]
    miss = client.post("/ai/tutor", json={"question": "Who won the 1998 world cup?"}, headers=s).json()
    assert miss["sources"] == []


def test_planner_prioritises_and_validates(client):
    t = _signup(client, "plan-teacher@example.com", "teacher")
    s = _signup(client, "plan-student@example.com")
    c, _ = _build_course(client, t)
    client.post(f"/courses/{c['id']}/enroll", headers=s)
    exam = (date.today() + timedelta(days=5)).isoformat()
    plan = client.post("/planner", json={"course_id": c["id"], "exam_date": exam, "minutes_per_day": 30}, headers=s).json()
    assert plan["days"] and plan["days"][0]["items"][0]["title"] == "Velocity"
    past = client.post("/planner", json={"course_id": c["id"], "exam_date": date.today().isoformat(), "minutes_per_day": 30}, headers=s)
    assert past.status_code == 400


def test_audit_log_records_logins_for_admin_only(client):
    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    if not db.query(User).filter_by(email="audit-admin@example.com").first():
        db.add(User(full_name="Aud Admin", email="audit-admin@example.com", hashed_password=hash_password("secret123"), role="admin"))
        db.commit()
    db.close()
    client.post("/auth/login", json={"email": "nobody-here@example.com", "password": "wrongwrong"})
    tok = client.post("/auth/login", json={"email": "audit-admin@example.com", "password": "secret123"}).json()["access_token"]
    logs = client.get("/admin/audit", headers={"Authorization": f"Bearer {tok}"}).json()
    actions = {l["action"] for l in logs}
    assert {"auth.login", "auth.login_failed"} <= actions
    stu = _signup(client, "audit-stu@example.com")
    assert client.get("/admin/audit", headers=stu).status_code == 403
