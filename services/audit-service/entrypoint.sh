#!/usr/bin/env sh
set -e

echo "[audit-service] Running alembic migrations..."
alembic upgrade head

echo "[audit-service] Starting uvicorn..."
exec uvicorn audit_service.main:app \
    --host 0.0.0.0 \
    --port 8004 \
    --proxy-headers \
    --forwarded-allow-ips="*"
