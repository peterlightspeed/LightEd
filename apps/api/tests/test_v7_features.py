"""Friendly tutor guidance, AI lesson drafting, leaderboard, certificates."""
from app.core.config import settings
from app.services import aigen
from tests.test_teacher_features import _build_course, _signup


def _offline(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)


def test_student_without_courses_gets_enrol_help_and_suggestions(client, monkeypatch):
    _offline(monkeypatch)
    t = _signup(client, "g-teacher@example.com", "teacher")
    _build_course(client, t)
    s = _signup(client, "g-student@example.com")
    r = client.post("/ai/tutor", json={"question": "explain acceleration please"}, headers=s).json()
    assert r["sources"] == [] and r["provider"] == "guide"
    assert "not enrolled" in r["answer"].lower() and "Enrol" in r["answer"]
    assert r["suggestions"], "should suggest catalogue courses"
    assert {"label": "Browse courses", "href": "/courses"} in r["actions"]


def test_enrolled_student_miss_still_gets_next_steps(client, monkeypatch):
    _offline(monkeypatch)
    t = _signup(client, "g2-teacher@example.com", "teacher")
    c, _ = _build_course(client, t)
    s = _signup(client, "g2-student@example.com")
    client.post(f"/courses/{c['id']}/enroll", headers=s)
    r = client.post("/ai/tutor", json={"question": "Who won the 1998 world cup?"}, headers=s).json()
    assert r["sources"] == [] and "couldn't find" in r["answer"].lower() and r["actions"]


def test_teacher_with_no_lessons_is_told_how_to_start(client, monkeypatch):
    _offline(monkeypatch)
    t = _signup(client, "g3-teacher@example.com", "teacher")
    r = client.post("/ai/tutor", json={"question": "how do I begin?"}, headers=t).json()
    assert "Create a course" in r["answer"] and "OpenStax" in r["answer"]


def test_draft_lesson_and_topics_teacher_only_with_offline_fallback(client, monkeypatch):
    _offline(monkeypatch)
    t = _signup(client, "d-teacher@example.com", "teacher")
    s = _signup(client, "d-student@example.com")
    assert client.post("/ai/draft-lesson", json={"title": "Atoms"}, headers=s).status_code == 403
    d = client.post("/ai/draft-lesson", json={"title": "Atoms", "course_title": "Chemistry"}, headers=t).json()
    assert d["provider"] == "offline" and "Atoms" in d["content"]
    tp = client.post("/ai/suggest-topics", json={"course_title": "Data Analysis"}, headers=t).json()
    assert len(tp["topics"]) >= 5


def test_draft_lesson_uses_gemini_json(monkeypatch):
    monkeypatch.setattr(aigen, "_gemini", lambda *a, **k: '```json\n{"summary":"S","content":"Body **x**"}\n```')
    assert aigen.draft_lesson("Atoms") == ("S", "Body **x**", "gemini")


def test_leaderboard_ranks_and_is_scoped_to_teacher(client):
    t = _signup(client, "lb-teacher@example.com", "teacher")
    other = _signup(client, "lb-other@example.com", "teacher")
    a, b = _signup(client, "lb-a@example.com"), _signup(client, "lb-b@example.com")
    c, l = _build_course(client, t)
    for h in (a, b):
        client.post(f"/courses/{c['id']}/enroll", headers=h)
    client.post(f"/lessons/{l['id']}/complete", headers=a)
    lb = client.get(f"/teacher/leaderboard?course_id={c['id']}", headers=t).json()
    assert lb["count"] == 2 and lb["leaders"][0]["rank"] == 1
    assert lb["leaders"][0]["points"] >= lb["leaders"][1]["points"]
    assert client.get(f"/teacher/leaderboard?course_id={c['id']}", headers=other).status_code == 404
    assert client.get("/teacher/leaderboard", headers=a).status_code == 403


def test_certificate_requires_completion_and_verifies_publicly(client):
    t = _signup(client, "c-teacher@example.com", "teacher")
    s = _signup(client, "c-student@example.com")
    c, l = _build_course(client, t)
    client.post(f"/courses/{c['id']}/enroll", headers=s)
    assert client.get(f"/courses/{c['id']}/certificate", headers=s).status_code == 403
    client.post(f"/lessons/{l['id']}/complete", headers=s)
    cert = client.get(f"/courses/{c['id']}/certificate", headers=s).json()
    assert cert["course_title"] and cert["certificate_id"].startswith("LE-")
    ok = client.get(f"/certificates/verify/{cert['certificate_id']}").json()
    assert ok["valid"] is True and ok["student_name"] == cert["student_name"]
    forged = cert["certificate_id"][:-1] + ("A" if cert["certificate_id"][-1] != "A" else "B")
    assert client.get(f"/certificates/verify/{forged}").json() == {"valid": False}
