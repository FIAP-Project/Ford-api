#!/usr/bin/env sh
set -e

echo "[user-service] Running alembic migrations..."
alembic upgrade head

echo "[user-service] Starting uvicorn..."
exec uvicorn user_service.main:app \
    --host 0.0.0.0 \
    --port 8002 \
    --proxy-headers \
    --forwarded-allow-ips="*"
