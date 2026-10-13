import os
import tempfile

import pytest

# Keep the generated secret key out of the real data directory
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="homelab-hub-test-"))

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402
from app.models import db  # noqa: E402
from app.utils import monitor  # noqa: E402


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AUTH_USERNAME = "admin"
    AUTH_PASSWORD = "secret"
    SECRET_KEY = "test"
    STATUS_SYNC = True  # run reachability checks inline instead of in the background thread


class OpenConfig(TestConfig):
    AUTH_PASSWORD = ""


@pytest.fixture
def app():
    app = create_app(TestConfig)
    monitor.reset_cache()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def anon(app):
    """Client without a session."""
    return app.test_client()


@pytest.fixture
def client(app):
    """Logged-in client."""
    c = app.test_client()
    res = c.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert res.status_code == 200
    return c


def create(client, kind, **fields):
    res = client.post(f"/api/{kind}", json=fields)
    assert res.status_code == 201, res.get_json()
    body = res.get_json()
    return body.get("data", body)  # /api/shares returns the object unwrapped
