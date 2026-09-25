from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from ford_shared.db import Database
from ford_shared.events import EventBus
from ford_shared.security.crypto import FieldCipher
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.repositories import ProfileRepository
from user_service.services import ProfileService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db: Database = request.app.state.database
    async for session in db.session():
        yield session


def get_field_cipher(request: Request) -> FieldCipher:
    return request.app.state.field_cipher


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus


def get_profile_service(
    session: AsyncSession = Depends(get_db_session),
    cipher: FieldCipher = Depends(get_field_cipher),
    event_bus: EventBus = Depends(get_event_bus),
) -> ProfileService:
    return ProfileService(ProfileRepository(session), cipher, event_bus)
