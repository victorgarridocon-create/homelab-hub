from app import auth, create_app

from .conftest import OpenConfig


def test_api_requires_login(anon):
    assert anon.get("/api/hardware").status_code == 401
    assert anon.get("/inventory/export").status_code == 401
    assert anon.get("/api/status").status_code == 401


def test_public_endpoints(anon):
    assert anon.get("/api/health").status_code == 200
    me = anon.get("/api/auth/me").get_json()
    assert me == {"authenticated": False, "auth_enabled": True, "user": None}


def test_login_logout(anon):
    res = anon.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert res.get_json()["authenticated"] is True
    assert anon.get("/api/hardware").status_code == 200

    anon.post("/api/auth/logout")
    assert anon.get("/api/hardware").status_code == 401


def test_wrong_password(anon):
    res = anon.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert res.status_code == 401
    assert anon.get("/api/hardware").status_code == 401


def test_lockout_after_repeated_failures(anon):
    auth._failed_attempts.clear()
    for _ in range(auth.MAX_ATTEMPTS):
        anon.post("/api/auth/login", json={"username": "admin", "password": "bad"})
    res = anon.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert res.status_code == 429
    auth._failed_attempts.clear()


def test_auth_disabled_without_password():
    c = create_app(OpenConfig).test_client()
    assert c.get("/api/hardware").status_code == 200
    assert c.get("/api/auth/me").get_json()["auth_enabled"] is False


def test_security_headers(anon):
    res = anon.get("/api/health")
    csp = res.headers["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "object-src 'none'" in csp
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
