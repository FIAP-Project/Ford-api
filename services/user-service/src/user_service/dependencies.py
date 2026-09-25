from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from ford_shared.db import Database
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.repositories import ProfileRepository
from user_service.services import ProfileService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db: Database = request.app.state.database
    async for session in db.session():
        yield session


def get_profile_service(session: AsyncSession = Depends(get_db_session)) -> ProfileService:
    return ProfileService(ProfileRepository(session))
