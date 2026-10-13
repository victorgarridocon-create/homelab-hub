import gzip
import os

from flask import Flask, jsonify, request, send_from_directory

from .config import Config
from .models import db

COMPRESSIBLE = {"application/json", "text/html", "text/css", "text/javascript", "application/javascript", "image/svg+xml"}

CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    # Svelte sets inline style attributes
    "style-src 'self' 'unsafe-inline'",
    # Icons: uploaded (data:) or picked from the dashboard-icons catalogue
    "img-src 'self' data: https:",
    "connect-src 'self' https://api.github.com https://raw.githubusercontent.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


def create_app(config_class=Config):
    # STATIC_DIR lets end-to-end tests serve frontend/dist without copying it into the backend
    static_dir = os.path.abspath(os.environ.get("STATIC_DIR") or os.path.join(os.path.dirname(__file__), "..", "static"))
    app = Flask(__name__, static_folder=static_dir, static_url_path="")

    app.config.from_object(config_class)

    db.init_app(app)

    # Enable CORS only for local development (the Vite dev server runs on another port)
    if os.environ.get("FLASK_ENV") != "production":
        try:
            from flask_cors import CORS
            CORS(app, supports_credentials=True)
        except ImportError:
            pass

    # Basic login: protects every API route when HUB_PASSWORD is set
    from . import auth
    app.register_blueprint(auth.bp)
    app.before_request(auth.require_login)
    if not app.config.get("AUTH_PASSWORD") and not app.config.get("TESTING"):
        app.logger.warning("HUB_PASSWORD is not set: login is DISABLED and the API is open to anyone.")

    # Register blueprints
    from .routes import register_blueprints
    register_blueprints(app)

    # Defence in depth against XSS: even if injected markup slips through, the browser
    # refuses inline scripts/handlers and scripts from other origins.
    @app.after_request
    def security_headers(response):
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    # Compress JSON and the built JS/CSS (lists and the map can be hundreds of KB)
    @app.after_request
    def compress(response):
        if (
            response.status_code != 200
            or "gzip" not in request.headers.get("Accept-Encoding", "")
            or response.headers.get("Content-Encoding")
            or response.mimetype not in COMPRESSIBLE
        ):
            return response
        response.direct_passthrough = False  # static files are streamed by default
        data = response.get_data()
        if len(data) < 1024:
            return response
        response.set_data(gzip.compress(data, compresslevel=5))
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Content-Length"] = str(len(response.get_data()))
        response.vary.add("Accept-Encoding")
        return response

    # Health check
    @app.route("/api/health")
    def health():
        return jsonify(status="ok")

    # SPA catch-all: serve index.html for all non-API routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        # Skip API routes - they're handled by blueprints
        if ("/" + path).startswith(auth.API_PREFIXES):
            return jsonify(error="Not found"), 404
        file_path = os.path.join(static_dir, path)
        if os.path.isfile(file_path):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, "index.html")

    # Create tables on first request if they don't exist
    with app.app_context():
        db.create_all()

    return app
