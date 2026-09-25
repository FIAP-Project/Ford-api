"""Fixtures for user-service HTTP integration tests.

Same approach as auth-service: real app + real RBAC/JWT dependency chain,
with the DB-backed ``ProfileRepository`` swapped for an in-memory fake via
``app.dependency_overrides``, so tests exercise real routing, real
``ProfileService`` logic and real ``require_role`` enforcement without a
live Postgres.
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from ford_shared.security.jwt import JWTService
from ford_shared.security.rbac import Role
from starlette.testclient import TestClient
from user_service.dependencies import get_profile_service
from user_service.main import app
from user_service.models import UserProfile
from user_service.services import ProfileService

JWT_SECRET = "test-jwt-secret-please-32-characters!!"


class FakeCipher:
    """Identity encrypt/decrypt: tests seed and assert plaintext directly."""

    def encrypt(self, value: str | None) -> str | None:
        return value

    def decrypt(self, value: str | None) -> str | None:
        return value


class FakeProfileRepository:
    def __init__(self) -> None:
        self.by_auth_user_id: dict = {}

    async def get_by_auth_user_id(self, auth_user_id):
        return self.by_auth_user_id.get(auth_user_id)

    async def list_all(self, limit: int = 100, offset: int = 0):
        rows = list(self.by_auth_user_id.values())
        return rows[offset : offset + limit]

    async def upsert_from_event(self, *, auth_user_id, email, role, full_name):
        existing = self.by_auth_user_id.get(auth_user_id)
        if existing is not None:
            existing.email = email
            existing.role = role
            if full_name is not None:
                existing.full_name = full_name
            return existing
        profile = UserProfile(
            id=uuid4(),
            auth_user_id=auth_user_id,
            email=email,
            role=role,
            full_name=full_name,
        )
        self.by_auth_user_id[auth_user_id] = profile
        return profile

    async def update_full_name(self, auth_user_id, full_name):
        profile = self.by_auth_user_id.get(auth_user_id)
        if profile is None:
            return None
        profile.full_name = full_name
        return profile

    async def update_role(self, auth_user_id, role):
        profile = self.by_auth_user_id.get(auth_user_id)
        if profile is None:
            return None
        profile.role = role
        return profile


@pytest.fixture
def profile_repo() -> FakeProfileRepository:
    return FakeProfileRepository()


@pytest.fixture
def jwt_service() -> JWTService:
    return JWTService(secret_key=JWT_SECRET)


@pytest.fixture
def client(profile_repo, jwt_service):
    app.state.jwt_service = jwt_service

    def _override_profile_service() -> ProfileService:
        return ProfileService(profile_repo, FakeCipher(), AsyncMock())

    app.dependency_overrides[get_profile_service] = _override_profile_service
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
