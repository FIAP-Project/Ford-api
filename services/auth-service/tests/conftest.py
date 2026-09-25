"""Fixtures for auth-service HTTP integration tests.

Strategy: exercise the real FastAPI app, real routing/RBAC/JWT dependency
chain and the real ``AuthService`` business logic, but swap the
repository/event-bus layer for lightweight in-memory fakes via
``app.dependency_overrides``. This avoids needing a live Postgres/RabbitMQ
while still testing genuine end-to-end request/response behavior (status
codes, error envelopes, token issuance).
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from auth_service.dependencies import get_auth_service, get_db_session
from auth_service.main import app
from auth_service.models import RefreshToken, User
from auth_service.services import AuthService
from ford_shared.security.jwt import JWTService
from sqlalchemy.exc import IntegrityError
from starlette.testclient import TestClient

JWT_SECRET = "test-jwt-secret-please-32-characters!!"


class FakeUserRepository:
    def __init__(self) -> None:
        self.by_email: dict[str, User] = {}
        self.by_id: dict = {}

    async def get_by_email(self, email):
        return self.by_email.get(email)

    async def get_by_id(self, user_id):
        return self.by_id.get(user_id)

    async def create(self, *, email, password_hash, role, full_name):
        if email in self.by_email:
            raise IntegrityError("duplicate email", params=None, orig=Exception("unique violation"))
        user = User(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            role=role,
            full_name=full_name,
        )
        self.by_email[email] = user
        self.by_id[user.id] = user
        return user


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self.by_jti: dict[str, RefreshToken] = {}

    async def create(self, *, user_id, jti, expires_at):
        token = RefreshToken(
            id=uuid4(), user_id=user_id, jti=jti, expires_at=expires_at, revoked=False
        )
        self.by_jti[jti] = token
        return token

    async def get_active(self, jti):
        token = self.by_jti.get(jti)
        if token is not None and not token.revoked:
            return token
        return None

    async def revoke(self, jti):
        if jti in self.by_jti:
            self.by_jti[jti].revoked = True


class FakeSession:
    """Stands in for AsyncSession.get(), used directly by GET /auth/me."""

    def __init__(self, users: FakeUserRepository) -> None:
        self._users = users

    async def get(self, model_cls, pk):
        return self._users.by_id.get(pk)


@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def refresh_repo() -> FakeRefreshTokenRepository:
    return FakeRefreshTokenRepository()


@pytest.fixture
def jwt_service() -> JWTService:
    return JWTService(secret_key=JWT_SECRET)


@pytest.fixture
def client(user_repo, refresh_repo, jwt_service):
    app.state.jwt_service = jwt_service
    app.state.limiter.reset()  # each test starts with a clean rate-limit bucket

    def _override_auth_service() -> AuthService:
        return AuthService(
            users=user_repo,
            refresh_tokens=refresh_repo,
            jwt=jwt_service,
            event_bus=AsyncMock(),
            refresh_ttl_days=7,
            access_ttl_minutes=15,
        )

    async def _override_db_session():
        yield FakeSession(user_repo)

    app.dependency_overrides[get_auth_service] = _override_auth_service
    app.dependency_overrides[get_db_session] = _override_db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
