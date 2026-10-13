#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
# One process (the status checker and login lockout live in memory) with threads, so a slow
# request never blocks the rest of the app
exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 wsgi:app
