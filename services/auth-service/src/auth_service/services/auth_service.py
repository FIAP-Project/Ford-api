"""Authentication use cases — orchestrates repositories, JWT and events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from auth_service.repositories import RefreshTokenRepository, UserRepository
from auth_service.schemas import RegisterRequest, TokenPair, UserOut
from ford_shared.events import (
    EventBus,
    EventType,
    UserLoggedInEvent,
    UserRegisteredEvent,
)
from ford_shared.events.schemas import AuthFailedEvent
from ford_shared.security import Role, hash_password, verify_password
from ford_shared.security.jwt import InvalidTokenError, JWTService


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        jwt: JWTService,
        event_bus: EventBus,
        refresh_ttl_days: int,
        access_ttl_minutes: int,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._jwt = jwt
        self._events = event_bus
        self._refresh_ttl = timedelta(days=refresh_ttl_days)
        self._access_ttl_seconds = access_ttl_minutes * 60

    async def register(self, payload: RegisterRequest) -> UserOut:
        try:
            user = await self._users.create(
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                role=Role.USER.value,
                full_name=payload.full_name,
            )
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            ) from exc

        await self._events.publish(
            EventType.USER_REGISTERED.value,
            UserRegisteredEvent(
                event_id=str(uuid4()),
                event_type=EventType.USER_REGISTERED,
                occurred_at=datetime.now(UTC),
                actor_user_id=str(user.id),
                user_id=str(user.id),
                email=user.email,
                role=user.role,
            ).model_dump(),
        )
        return UserOut.model_validate(user)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email.lower())
        if user is None or not verify_password(password, user.password_hash):
            await self._publish_auth_failed(email, "invalid_credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access, _ = self._jwt.issue_access(
            user_id=str(user.id), email=user.email, role=Role(user.role)
        )
        refresh, refresh_jti = self._jwt.issue_refresh(
            user_id=str(user.id), email=user.email, role=Role(user.role)
        )
        await self._refresh_tokens.create(
            user_id=user.id,
            jti=refresh_jti,
            expires_at=datetime.now(UTC) + self._refresh_ttl,
        )

        await self._events.publish(
            EventType.USER_LOGGED_IN.value,
            UserLoggedInEvent(
                event_id=str(uuid4()),
                event_type=EventType.USER_LOGGED_IN,
                occurred_at=datetime.now(UTC),
                actor_user_id=str(user.id),
                user_id=str(user.id),
                email=user.email,
            ).model_dump(),
        )

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=self._access_ttl_seconds,
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = self._jwt.decode(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc

        stored = await self._refresh_tokens.get_active(payload.jti)
        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or unknown",
            )

        # Rotate: revoke old, issue new pair.
        await self._refresh_tokens.revoke(payload.jti)

        access, _ = self._jwt.issue_access(
            user_id=payload.sub, email=payload.email, role=payload.role
        )
        new_refresh, new_jti = self._jwt.issue_refresh(
            user_id=payload.sub, email=payload.email, role=payload.role
        )
        await self._refresh_tokens.create(
            user_id=stored.user_id,
            jti=new_jti,
            expires_at=datetime.now(UTC) + self._refresh_ttl,
        )
        return TokenPair(
            access_token=access,
            refresh_token=new_refresh,
            expires_in=self._access_ttl_seconds,
        )

    async def _publish_auth_failed(self, email: str, reason: str) -> None:
        await self._events.publish(
            EventType.AUTH_FAILED.value,
            AuthFailedEvent(
                event_id=str(uuid4()),
                event_type=EventType.AUTH_FAILED,
                occurred_at=datetime.now(UTC),
                email=email,
                reason=reason,
            ).model_dump(),
        )
