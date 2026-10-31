"""Gemini client resilience + tutor behaviour (chips, follow-ups, honest offline notice)."""
import httpx

from app.core.config import settings
from app.services import aigen
from tests.test_teacher_features import _build_course, _signup


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code, self._p = status, payload or {}
        self.is_success = 200 <= status < 300
        self.text, self.content = str(payload), b"x"

    def json(self):
        return self._p


def _ok(text):
    return _Resp(200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})


def _reset(monkeypatch, key="test-key", model="gemini-1.5-flash"):
    monkeypatch.setattr(settings, "gemini_api_key", key)
    monkeypatch.setattr(settings, "gemini_model", model)
    monkeypatch.setattr(aigen, "_working_model", None)


def test_retired_model_falls_through_to_working_one_and_key_stays_out_of_url(monkeypatch):
    _reset(monkeypatch)
    seen = []

    def fake_post(url, headers=None, json=None, timeout=None, **kw):
        seen.append((url, headers))
        return _Resp(404) if "1.5-flash" in url else _ok("hello")

    monkeypatch.setattr(httpx, "post", fake_post)
    text, err = aigen._gemini_call("hi")
    assert text == "hello" and err is None
    assert aigen._working_model == "gemini-3.8-flash"
    assert all("key=" not in url for url, _ in seen), "API key must never be in the URL"
    assert all(h["x-goog-api-key"] == "test-key" for _, h in seen)
    # later calls go straight to the model that worked
    assert aigen._model_chain()[0] == "gemini-3.8-flash"


def test_bad_key_reports_clear_error_without_trying_every_model(monkeypatch):
    _reset(monkeypatch)
    calls = []
    monkeypatch.setattr(httpx, "post", lambda url, **kw: calls.append(url) or _Resp(403, {"error": {"message": "API key not valid"}}))
    text, err = aigen._gemini_call("hi")
    assert text is None and "403" in err and "API key not valid" in err
    assert len(calls) == 1


def test_missing_key_is_reported(monkeypatch):
    _reset(monkeypatch, key=None)
    assert aigen.gemini_status() == {"configured": False, "model": None, "ok": False,
                                     "error": "GEMINI_API_KEY is not set on the server"}


def test_chips_and_followups_use_context_instead_of_failing(client, monkeypatch):
    _reset(monkeypatch, key=None)  # offline mode
    t = _signup(client, "chip-teacher@example.com", "teacher")
    s = _signup(client, "chip-student@example.com")
    c, _ = _build_course(client, t)
    client.post(f"/courses/{c['id']}/enroll", headers=s)

    # A generic chip with no history -> overview of the student's courses, not "couldn't find that".
    r = client.post("/ai/tutor", json={"question": "What should I focus on first?"}, headers=s).json()
    assert r["sources"] and "couldn't find" not in r["answer"].lower()

    # "Explain this in simple words" after an acceleration question stays on acceleration.
    hist = [{"role": "user", "text": "What is acceleration?"}, {"role": "tutor", "text": "..."}]
    r = client.post("/ai/tutor", json={"question": "Explain this in simple words", "history": hist}, headers=s).json()
    assert "velocity" in r["answer"].lower() and r["sources"]

    # Inflected words still match (accelerating -> acceleration)
    r = client.post("/ai/tutor", json={"question": "why do objects keep accelerating"}, headers=s).json()
    assert r["sources"]

    # Real off-topic questions are still refused with no sources
    miss = client.post("/ai/tutor", json={"question": "Who won the 1998 world cup?"}, headers=s).json()
    assert miss["sources"] == []


def test_offline_fallback_tells_the_student_why(client, monkeypatch):
    _reset(monkeypatch, key="k")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp(503))
    monkeypatch.setattr(aigen.time, "sleep", lambda *_: None)
    t = _signup(client, "note-teacher@example.com", "teacher")
    s = _signup(client, "note-student@example.com")
    c, _ = _build_course(client, t)
    client.post(f"/courses/{c['id']}/enroll", headers=s)
    r = client.post("/ai/tutor", json={"question": "What is acceleration?"}, headers=s).json()
    assert r["provider"] == "offline" and r["notice"] and r["sources"]


def test_ai_status_requires_login_and_never_leaks_key(client, monkeypatch):
    _reset(monkeypatch, key="super-secret")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _ok("ok"))
    assert client.get("/ai/status").status_code in (401, 403)
    s = _signup(client, "status-student@example.com")
    r = client.get("/ai/status", headers=s)
    assert r.status_code == 200 and r.json()["ok"] is True
    assert "super-secret" not in r.text
