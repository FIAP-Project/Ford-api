"""FastAPI dependencies: DB session and AuthService wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.repositories import RefreshTokenRepository, UserRepository
from auth_service.services import AuthService
from ford_shared.db import Database
from ford_shared.events import EventBus
from ford_shared.security.jwt import JWTService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db: Database = request.app.state.database
    async for session in db.session():
        yield session


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus


def get_jwt(request: Request) -> JWTService:
    return request.app.state.jwt_service


def get_auth_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    jwt: JWTService = Depends(get_jwt),
) -> AuthService:
    settings = request.app.state.settings
    return AuthService(
        users=UserRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        jwt=jwt,
        event_bus=event_bus,
        refresh_ttl_days=settings.refresh_token_ttl_days,
        access_ttl_minutes=settings.access_token_ttl_minutes,
    )


