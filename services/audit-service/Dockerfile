FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY packages/shared/pyproject.toml /app/packages/shared/pyproject.toml
COPY services/audit-service/pyproject.toml /app/services/audit-service/pyproject.toml
COPY packages/shared /app/packages/shared
COPY services/audit-service /app/services/audit-service

RUN uv sync --frozen --package audit-service || uv sync --package audit-service

ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app/services/audit-service
COPY services/audit-service/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8004
ENTRYPOINT ["/entrypoint.sh"]
