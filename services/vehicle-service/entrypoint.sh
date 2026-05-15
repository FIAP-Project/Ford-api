#!/usr/bin/env sh
set -e

echo "[vehicle-service] Running alembic migrations..."
alembic upgrade head

echo "[vehicle-service] Starting uvicorn..."
exec uvicorn vehicle_service.main:app \
    --host 0.0.0.0 \
    --port 8003 \
    --proxy-headers \
    --forwarded-allow-ips="*"
