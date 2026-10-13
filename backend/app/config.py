import os
import secrets
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _data_dir():
    """Directory for persistent files (DB, secret key). /data inside Docker."""
    path = os.environ.get("DATA_DIR")
    if not path:
        path = "/data" if os.path.isdir("/data") else os.path.join(basedir, "..", "..", "data")
    return os.path.abspath(path)


def _load_secret_key():
    """Use SECRET_KEY from env, or generate one and persist it so sessions survive restarts."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    key_file = os.path.join(_data_dir(), ".secret_key")
    try:
        with open(key_file) as f:
            key = f.read().strip()
        if key:
            return key
    except FileNotFoundError:
        pass
    key = secrets.token_hex(32)
    try:
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, "w") as f:
            f.write(key)
        os.chmod(key_file, 0o600)
    except OSError:
        pass  # Fall back to an in-memory key (sessions reset on restart)
    return key


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, '..', '..', 'data', 'homelab-hub.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Allow larger request bodies for base64 image uploads (5MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Basic login. Auth is disabled when HUB_PASSWORD is empty.
    AUTH_USERNAME = os.environ.get("HUB_USERNAME", "admin")
    AUTH_PASSWORD = os.environ.get("HUB_PASSWORD", "")
    SECRET_KEY = _load_secret_key()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get("SESSION_DAYS", "30")))

    # Status monitoring: background checks every STATUS_INTERVAL_SECONDS (and on demand)
    STATUS_INTERVAL_SECONDS = int(os.environ.get("STATUS_INTERVAL_SECONDS", "60"))
    STATUS_TIMEOUT_SECONDS = float(os.environ.get("STATUS_TIMEOUT_SECONDS", "2"))
