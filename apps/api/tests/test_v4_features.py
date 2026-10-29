"""Join codes, notifications, resources, PDF import, password reset, rate limiting, catalogue top-up."""
import re

from app.core.config import settings


def _signup(client, email, role="student", name=None):
    r = client.post("/auth/register", json={"full_name": name or email.split("@")[0].title(), "email": email,
                                            "password": "secret123", "role": role})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _course(client, t):
    c = client.post("/courses", json={"title": "V4 Course", "description": "d"}, headers=t).json()
    tp = client.post(f"/courses/{c['id']}/topics", json={"title": "Topic", "order_index": 1}, headers=t).json()
    l = client.post("/lessons", json={"topic_id": tp["id"], "title": "Lesson One", "summary": "s",
                                      "content": "Photosynthesis converts sunlight into chemical energy inside chloroplasts.",
                                      "duration_minutes": 5, "order_index": 1}, headers=t).json()
    return c, l


def test_catalogue_top_up_adds_missing_courses_once(client):
    from app.db.catalog_extra import EXTRA, ensure_extra_courses
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        first = ensure_extra_courses(db)
        assert ensure_extra_courses(db) == 0  # idempotent
        assert first <= len(EXTRA)
    finally:
        db.close()
    titles = {c["title"] for c in client.get("/courses").json()}
    assert {e["title"] for e in EXTRA} <= titles


def test_join_code_flow_and_notifications(client):
    t = _signup(client, "v4-teacher@example.com", "teacher")
    s = _signup(client, "v4-student@example.com", name="Join Student")
    other = _signup(client, "v4-other@example.com", "teacher")
    c, l = _course(client, t)

    code = client.get(f"/courses/{c['id']}/join-code", headers=t).json()["code"]
    assert len(code) == 6
    assert client.get(f"/courses/{c['id']}/join-code", headers=t).json()["code"] == code  # stable
    assert client.get(f"/courses/{c['id']}/join-code", headers=other).status_code == 403
    assert client.get(f"/courses/{c['id']}/join-code", headers=s).status_code == 403
    assert client.post("/courses/join", json={"code": "ZZZZZZ"}, headers=s).status_code == 404

    joined = client.post("/courses/join", json={"code": code.lower()}, headers=s)
    assert joined.status_code == 200 and joined.json()["course_id"] == c["id"]
    assert client.post("/courses/join", json={"code": code}, headers=s).status_code == 200  # idempotent

    new = client.post(f"/courses/{c['id']}/join-code/reset", headers=t).json()["code"]
    assert new != code
    assert client.post("/courses/join", json={"code": code}, headers=s).status_code == 404  # old code dead

    # teacher got exactly one "joined" notification
    n = client.get("/notifications", headers=t).json()
    assert n["unread"] >= 1 and any("Join Student" in i["body"] for i in n["items"])

    # publishing a quiz notifies enrolled students
    q = client.put(f"/lessons/{l['id']}/quiz", json={"questions": [
        {"prompt": "Q", "options": ["a", "b"], "answer_index": 0}]}, headers=t).json()
    sn = client.get("/notifications", headers=s).json()
    assert any(i["kind"] == "quiz" for i in sn["items"])

    # a failing attempt alerts the teacher
    client.post(f"/quizzes/{q['id']}/attempts", json={"answers": [1]}, headers=s)
    tn = client.get("/notifications", headers=t).json()
    assert any(i["kind"] == "risk" for i in tn["items"])

    assert client.post("/notifications/read-all", headers=t).status_code == 200
    assert client.get("/notifications", headers=t).json()["unread"] == 0


def test_lesson_resources(client):
    t = _signup(client, "res-teacher@example.com", "teacher")
    s = _signup(client, "res-student@example.com")
    _, l = _course(client, t)
    r = client.post(f"/lessons/{l['id']}/resources", json={"title": "Khan Academy", "url": "https://www.khanacademy.org/"}, headers=t)
    assert r.status_code == 201
    assert client.post(f"/lessons/{l['id']}/resources", json={"title": "bad", "url": "javascript:alert(1)"}, headers=t).status_code == 422
    assert client.post(f"/lessons/{l['id']}/resources", json={"title": "x y", "url": "https://a.io"}, headers=s).status_code == 403
    assert len(client.get(f"/lessons/{l['id']}/resources", headers=s).json()) == 1
    assert client.delete(f"/resources/{r.json()['id']}", headers=t).status_code == 200


def _make_pdf(text: str) -> bytes:
    """Build a small VALID PDF (with a correct xref table) containing `text`."""
    objs = [
        "<</Type/Catalog/Pages 2 0 R>>",
        "<</Type/Pages/Kids[3 0 R]/Count 1>>",
        "<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
        None,
        "<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    stream = f"BT /F1 12 Tf 10 50 Td ({text}) Tj ET"
    objs[3] = f"<</Length {len(stream)}>>\nstream\n{stream}\nendstream"
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<</Size {len(objs) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF".encode()
    return out


def test_pdf_import(client):
    t = _signup(client, "pdf-teacher@example.com", "teacher")
    s = _signup(client, "pdf-student@example.com")
    pdf = _make_pdf("Hello LightEd")
    ok = client.post("/materials/extract-pdf", files={"file": ("a.pdf", pdf, "application/pdf")}, headers=t)
    assert ok.status_code == 200 and "Hello LightEd" in ok.json()["text"], ok.text
    assert client.post("/materials/extract-pdf", files={"file": ("a.txt", b"hello", "text/plain")}, headers=t).status_code == 400
    assert client.post("/materials/extract-pdf", files={"file": ("a.pdf", pdf, "application/pdf")}, headers=s).status_code == 403


def test_password_reset_flow(client, monkeypatch):
    sent = {}
    from app.api.routes import extras

    monkeypatch.setattr(extras, "send_email", lambda to, subject, body: sent.update(to=to, body=body))
    _signup(client, "reset-me@example.com")
    # unknown email gives the SAME response (no enumeration)
    a = client.post("/auth/forgot-password", json={"email": "ghost@example.com"}).json()
    b = client.post("/auth/forgot-password", json={"email": "reset-me@example.com"}).json()
    assert a == b and sent["to"] == "reset-me@example.com"
    token = re.search(r"token=([\w\-]+)", sent["body"]).group(1)

    assert client.post("/auth/reset-password", json={"token": "x" * 30, "password": "newsecret1"}).status_code == 400
    assert client.post("/auth/reset-password", json={"token": token, "password": "short"}).status_code == 422
    assert client.post("/auth/reset-password", json={"token": token, "password": "newsecret1"}).status_code == 200
    assert client.post("/auth/reset-password", json={"token": token, "password": "another123"}).status_code == 400  # single use
    assert client.post("/auth/login", json={"email": "reset-me@example.com", "password": "newsecret1"}).status_code == 200
    assert client.post("/auth/login", json={"email": "reset-me@example.com", "password": "secret123"}).status_code == 401


def test_login_rate_limit(client, monkeypatch):
    from app.core import ratelimit

    ratelimit._hits.clear()
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    codes = [client.post("/auth/login", json={"email": "rl@example.com", "password": "whatever1"}).status_code for _ in range(12)]
    assert codes[:10] == [401] * 10 and 429 in codes[10:]
    ratelimit._hits.clear()


def test_live_classes_flow(client):
    from datetime import datetime, timedelta, timezone

    t = _signup(client, "live-teacher@example.com", "teacher")
    s = _signup(client, "live-student@example.com", name="Live Student")
    outsider = _signup(client, "live-outsider@example.com")
    c, _ = _course(client, t)
    client.post(f"/courses/{c['id']}/enroll", headers=s)
    soon = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    later = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    body = {"title": "Week 1: Photosynthesis", "starts_at": soon, "duration_minutes": 45, "link": "https://meet.google.com/abc-defg-hij"}

    assert client.post(f"/courses/{c['id']}/sessions", json=body, headers=s).status_code == 403      # students can't schedule
    assert client.post(f"/courses/{c['id']}/sessions", json={**body, "starts_at": past}, headers=t).status_code == 400
    assert client.post(f"/courses/{c['id']}/sessions", json={**body, "link": "javascript:alert(1)"}, headers=t).status_code == 422
    made = client.post(f"/courses/{c['id']}/sessions", json=body, headers=t)
    assert made.status_code == 201 and made.json()["status"] == "live"   # starts in 5 min -> doors open
    client.post(f"/courses/{c['id']}/sessions", json={**body, "title": "Week 2 recap", "starts_at": later}, headers=t)

    listed = client.get(f"/courses/{c['id']}/sessions", headers=s).json()
    assert [i["status"] for i in listed] == ["live", "upcoming"]
    assert client.get(f"/courses/{c['id']}/sessions", headers=outsider).status_code == 403          # not enrolled
    assert any(n["kind"] == "live" for n in client.get("/notifications", headers=s).json()["items"])
    assert len(client.get("/sessions/upcoming", headers=s).json()) == 2
    assert client.get("/sessions/upcoming", headers=outsider).json() == []

    assert client.delete(f"/sessions/{made.json()['id']}", headers=s).status_code == 403
    assert client.delete(f"/sessions/{made.json()['id']}", headers=t).status_code == 200
