def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_register_and_login(client):
    payload = {
        "full_name": "Test Student",
        "email": "student@example.com",
        "password": "secret123",
        "role": "student",
    }
    res = client.post("/auth/register", json=payload)
    assert res.status_code in (201, 400)  # 400 if re-run

    res = client.post("/auth/login", json={"email": payload["email"], "password": "secret123"})
    assert res.status_code == 200
    assert "access_token" in res.json()


# ---------------------------------------------------------------- CORS / robustness
def test_cors_preflight_allows_vercel_origin(client):
    """The exact failing case from production: browser preflight from the Vercel app."""
    res = client.options(
        "/auth/register",
        headers={
            "Origin": "https://light-ed.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "https://light-ed.vercel.app"


def test_cors_blocks_unknown_origin(client):
    res = client.options(
        "/auth/register",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in res.headers


def test_origin_list_is_normalised():
    from app.core.config import Settings

    s = Settings(backend_cors_origins=' "https://a.vercel.app/" , http://localhost:3000 ', frontend_url="https://b.app/")
    assert s.cors_origins == ["https://a.vercel.app", "http://localhost:3000", "https://b.app"]


def test_email_is_case_insensitive(client):
    body = {"full_name": "Case Test", "email": "CaseTest@Example.com", "password": "secret123", "role": "student"}
    assert client.post("/auth/register", json=body).status_code in (201, 400)
    res = client.post("/auth/register", json={**body, "email": "casetest@example.com"})
    assert res.status_code == 400  # duplicate, not a second account


# ---------------------------------------------------------------- Google auth
def test_google_login_creates_user_and_blocks_password_login(client, monkeypatch):
    from app.api.routes import auth as auth_routes
    from app.core.config import settings

    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(
        auth_routes,
        "verify_google_credential",
        lambda cred: {"email": "g.user@gmail.com", "name": "Google User", "picture": "http://x/y.png"},
    )
    res = client.post("/auth/google", json={"credential": "fake", "role": "teacher"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "teacher" and data["access_token"]

    # Same Google account again -> same user (no duplicate).
    again = client.post("/auth/google", json={"credential": "fake"}).json()
    assert again["user"]["id"] == data["user"]["id"]

    # Password-less account must give a clear 401, not a 500.
    res = client.post("/auth/login", json={"email": "g.user@gmail.com", "password": "whatever1"})
    assert res.status_code == 401 and "Google" in res.json()["detail"]


def test_google_not_configured_returns_501(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "google_client_id", None)
    assert client.post("/auth/google", json={"credential": "x"}).status_code == 501


def test_server_errors_still_carry_cors_headers():
    """A crash must surface as a JSON 500 *with* CORS headers (not a fake CORS error)."""
    from fastapi.testclient import TestClient

    from app.main import app

    @app.get("/__boom")
    def boom():  # pragma: no cover - raises on purpose
        raise RuntimeError("boom")

    res = TestClient(app, raise_server_exceptions=False).get(
        "/__boom", headers={"Origin": "https://light-ed.vercel.app"}
    )
    assert res.status_code == 500
    assert res.headers["access-control-allow-origin"] == "https://light-ed.vercel.app"
