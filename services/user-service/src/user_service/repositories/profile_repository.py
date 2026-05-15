from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.models import UserProfile


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_auth_user_id(self, auth_user_id: UUID) -> UserProfile | None:
        result = await self._session.execute(
            select(UserProfile).where(UserProfile.auth_user_id == auth_user_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> Sequence[UserProfile]:
        result = await self._session.execute(
            select(UserProfile).order_by(UserProfile.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def upsert_from_event(
        self,
        *,
        auth_user_id: UUID,
        email: str,
        role: str,
        full_name: str | None,
    ) -> UserProfile:
        existing = await self.get_by_auth_user_id(auth_user_id)
        if existing is not None:
            existing.email = email
            existing.role = role
            if full_name is not None:
                existing.full_name = full_name
            await self._session.flush()
            return existing
        profile = UserProfile(
            auth_user_id=auth_user_id,
            email=email,
            role=role,
            full_name=full_name,
        )
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def update_full_name(
        self, auth_user_id: UUID, full_name: str | None
    ) -> UserProfile | None:
        profile = await self.get_by_auth_user_id(auth_user_id)
        if profile is None:
            return None
        profile.full_name = full_name
        await self._session.flush()
        return profile

    async def update_role(self, auth_user_id: UUID, role: str) -> UserProfile | None:
        profile = await self.get_by_auth_user_id(auth_user_id)
        if profile is None:
            return None
        profile.role = role
        await self._session.flush()
        return profile
