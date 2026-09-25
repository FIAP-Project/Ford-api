"""Fixtures for audit-service HTTP integration tests.

Same approach as the other services: real app + real RBAC/JWT dependency
chain and real ``AuditService`` logic, with the DB-backed
``EventRepository`` swapped for an in-memory fake via
``app.dependency_overrides``.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from audit_service.dependencies import get_audit_service
from audit_service.main import app
from audit_service.models import AuditEvent
from audit_service.services import AuditService
from ford_shared.security.jwt import JWTService
from ford_shared.security.rbac import Role

JWT_SECRET = "test-jwt-secret-please-32-characters!!"


class FakeEventRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def append(
        self, *, event_type, routing_key, actor_user_id, payload, occurred_at, signature
    ):
        event = AuditEvent(
            id=uuid4(),
            event_type=event_type,
            routing_key=routing_key,
            actor_user_id=actor_user_id,
            payload=payload,
            occurred_at=occurred_at,
            signature=signature,
        )
        self.events.append(event)
        return event

    async def list(self, *, event_type=None, actor_user_id=None, limit=100, offset=0):
        rows = self.events
        if event_type:
            rows = [e for e in rows if e.event_type == event_type]
        if actor_user_id:
            rows = [e for e in rows if e.actor_user_id == actor_user_id]
        rows = sorted(rows, key=lambda e: e.occurred_at, reverse=True)
        return rows[offset : offset + limit]


@pytest.fixture
def event_repo() -> FakeEventRepository:
    return FakeEventRepository()


@pytest.fixture
def jwt_service() -> JWTService:
    return JWTService(secret_key=JWT_SECRET)


@pytest.fixture
def client(event_repo, jwt_service):
    app.state.jwt_service = jwt_service

    def _override_audit_service() -> AuditService:
        return AuditService(event_repo)

    app.dependency_overrides[get_audit_service] = _override_audit_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_token(jwt_service):
    """Factory fixture: issue a real access token for a given role."""

    def _make(*, user_id=None, email="user@example.com", role=Role.USER):
        user_id = user_id or uuid4()
        token, _ = jwt_service.issue_access(user_id=str(user_id), email=email, role=role)
        return user_id, {"Authorization": f"Bearer {token}"}

    return _make
