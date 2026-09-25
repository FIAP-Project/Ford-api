"""Fixtures for vehicle-service HTTP integration tests.

Same approach as auth/user-service: real app + real RBAC/JWT dependency
chain and real ``VehicleService`` business logic, with the DB-backed
``QueryRepository`` swapped for an in-memory fake and the Anthropic-backed
``ClaudeClient`` swapped for a stub, via ``app.dependency_overrides``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from ford_shared.security.jwt import JWTService
from ford_shared.security.rbac import Role
from vehicle_service.dependencies import get_vehicle_service
from vehicle_service.main import app
from vehicle_service.models import VehicleQuery, VehicleSpec
from vehicle_service.services.claude_client import ClaudeResult, ClaudeSpec
from vehicle_service.services.vehicle_service import VehicleService

JWT_SECRET = "test-jwt-secret-please-32-characters!!"


class FakeQueryRepository:
    def __init__(self) -> None:
        self.by_id: dict = {}

    async def create(self, *, user_id, brand, model, version, attributes):
        query = VehicleQuery(
            id=uuid4(),
            user_id=user_id,
            brand=brand,
            model=model,
            version=version,
            requested_attrs=attributes,
            status="pending",
        )
        query.created_at = datetime.now(UTC)
        query.specs = []
        self.by_id[query.id] = query
        return query

    async def attach_specs(self, query, specs):
        for spec in specs:
            query.specs.append(
                VehicleSpec(
                    query_id=query.id,
                    attribute=spec.attribute,
                    value=spec.value,
                    available=spec.available,
                    normalized_unit=spec.normalized_unit,
                    source_hint=spec.source_hint,
                )
            )

    async def mark_completed(self, query, raw_response):
        query.status = "completed"
        query.raw_response = raw_response

    async def mark_failed(self, query, error):
        query.status = "failed"
        query.error_message = error[:500]

    async def get(self, query_id):
        return self.by_id.get(query_id)

    async def list_by_user(self, user_id, limit, offset):
        rows = [q for q in self.by_id.values() if q.user_id == user_id]
        rows.sort(key=lambda q: q.created_at, reverse=True)
        return rows[offset : offset + limit]

    async def list_all(self, limit, offset):
        rows = sorted(self.by_id.values(), key=lambda q: q.created_at, reverse=True)
        return rows[offset : offset + limit]


class FakeClaudeClient:
    """Stub Claude client: returns canned specs unless configured to fail."""

    def __init__(self) -> None:
        self.should_fail = False

    async def fetch_vehicle_specs(self, *, brand, model, version, attributes):
        if self.should_fail:
            raise RuntimeError("upstream Claude API failure")
        specs = [
            ClaudeSpec(
                attribute=attr,
                value="123",
                available=True,
                normalized_unit=None,
                source_hint="stub",
            )
            for attr in attributes
        ]
        return ClaudeResult(specs=specs, raw_response={"model": "stub", "stop_reason": "tool_use"})


@pytest.fixture
def query_repo() -> FakeQueryRepository:
    return FakeQueryRepository()


@pytest.fixture
def claude_client() -> FakeClaudeClient:
    return FakeClaudeClient()


@pytest.fixture
def jwt_service() -> JWTService:
    return JWTService(secret_key=JWT_SECRET)


@pytest.fixture
def client(query_repo, claude_client, jwt_service):
    app.state.jwt_service = jwt_service
    app.state.limiter.reset()  # each test starts with a clean rate-limit bucket

    def _override_vehicle_service() -> VehicleService:
        return VehicleService(
            repo=query_repo, claude=claude_client, event_bus=AsyncMock()
        )

    app.dependency_overrides[get_vehicle_service] = _override_vehicle_service
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
