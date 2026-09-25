"""Repo-wide pytest bootstrap.

Every service's ``main`` module builds its FastAPI app (and therefore its
``Settings``) at import time, so the required environment variables must
exist *before* any test module imports ``<service>.main``. Since this is a
single uv workspace with one pytest session covering every service
(``testpaths = ["packages", "services"]``), we set sane test defaults here,
at module import time, so they are in place no matter which service's tests
get collected first.

Values are irrelevant beyond satisfying `pydantic-settings` validation:
integration tests never open a real Postgres/RabbitMQ connection — every
service-level test overrides the DB/event-bus dependencies with fakes.
"""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/ford_test"
)
os.environ.setdefault("AMQP_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("EVENT_SIGNING_SECRET", "test-signing-secret-please-32-chars!!")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-please-32-characters!!")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key-not-called-in-tests")
