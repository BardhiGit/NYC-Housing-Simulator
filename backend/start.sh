#!/bin/sh
# Production startup: run migrations, then start the server.
# Railway injects $PORT; default to 8000 for local/Docker.

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server on port ${PORT:-8000}..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 2 \
  --log-level info
