#!/bin/sh
# Serves the built frontend (frontend/dist) from Flask with a throwaway database for the e2e tests.
# PYTHON can point at a virtualenv interpreter that has backend/requirements.txt installed.
set -e
cd "$(dirname "$0")/../../backend"
DATA_DIR="$(mktemp -d)"
export DATA_DIR
export DATABASE_URL="sqlite:///$DATA_DIR/e2e.db"
export STATIC_DIR="$(cd ../frontend/dist && pwd)"
export HUB_USERNAME=admin
export HUB_PASSWORD=e2e-secret
export FLASK_ENV=production
exec "${PYTHON:-python3}" -m flask --app wsgi run --port "${E2E_PORT:-5055}"
