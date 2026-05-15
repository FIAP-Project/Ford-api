#!/usr/bin/env sh
set -e

echo "[auth-service] Running alembic migrations..."
alembic upgrade head

echo "[auth-service] Starting uvicorn..."
exec uvicorn auth_service.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --proxy-headers \
    --forwarded-allow-ips="*"
