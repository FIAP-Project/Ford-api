FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

WORKDIR /app

# Copy workspace manifests first for layer caching.
COPY pyproject.toml /app/pyproject.toml
COPY packages/shared/pyproject.toml /app/packages/shared/pyproject.toml
COPY services/auth-service/pyproject.toml /app/services/auth-service/pyproject.toml

# Source for editable workspace installs.
COPY packages/shared /app/packages/shared
COPY services/auth-service /app/services/auth-service

RUN uv sync --frozen --package auth-service || uv sync --package auth-service

ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app/services/auth-service
COPY services/auth-service/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8001
ENTRYPOINT ["/entrypoint.sh"]
