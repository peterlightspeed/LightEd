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
