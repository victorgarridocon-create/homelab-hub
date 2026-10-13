"""Basic single-user login backed by a signed session cookie."""
import hmac
import time
from collections import defaultdict

from flask import Blueprint, current_app, jsonify, request, session

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Paths handled by the API (everything else is the SPA and stays public so the login page can load)
API_PREFIXES = ("/api/", "/inventory")
PUBLIC_PATHS = ("/api/auth/", "/api/health")

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
_failed_attempts = defaultdict(list)  # ip -> [timestamps]


def auth_enabled():
    return bool(current_app.config.get("AUTH_PASSWORD"))


def _client_ip():
    # X-Forwarded-For is not trusted: it can be spoofed to bypass the lockout
    return request.remote_addr or ""


def _is_locked_out(ip):
    now = time.time()
    _failed_attempts[ip] = [t for t in _failed_attempts[ip] if now - t < LOCKOUT_SECONDS]
    return len(_failed_attempts[ip]) >= MAX_ATTEMPTS


def require_login():
    """before_request hook: reject unauthenticated API calls."""
    if not auth_enabled() or request.method == "OPTIONS":
        return None
    path = request.path
    if not path.startswith(API_PREFIXES) or path.startswith(PUBLIC_PATHS):
        return None
    if session.get("user"):
        return None
    return jsonify(error="Authentication required"), 401


@bp.route("/me", methods=["GET"])
def me():
    if not auth_enabled():
        return jsonify(authenticated=True, auth_enabled=False, user=None)
    user = session.get("user")
    return jsonify(authenticated=bool(user), auth_enabled=True, user=user)


@bp.route("/login", methods=["POST"])
def login():
    if not auth_enabled():
        return jsonify(authenticated=True, auth_enabled=False, user=None)

    ip = _client_ip()
    if _is_locked_out(ip):
        return jsonify(error="Too many attempts. Try again later."), 429

    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))
    password = str(data.get("password", ""))
    valid_user = hmac.compare_digest(username.encode(), current_app.config["AUTH_USERNAME"].encode())
    valid_pass = hmac.compare_digest(password.encode(), current_app.config["AUTH_PASSWORD"].encode())

    if not (valid_user and valid_pass):
        _failed_attempts[ip].append(time.time())
        return jsonify(error="Invalid username or password"), 401

    _failed_attempts.pop(ip, None)
    session.clear()
    session.permanent = True
    session["user"] = username
    return jsonify(authenticated=True, auth_enabled=True, user=username)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(authenticated=False, auth_enabled=auth_enabled(), user=None)
