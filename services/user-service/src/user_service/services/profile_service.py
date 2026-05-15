from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status

from user_service.repositories import ProfileRepository
from user_service.schemas import ProfileOut


class ProfileService:
    def __init__(self, repo: ProfileRepository) -> None:
        self._repo = repo

    async def get(self, auth_user_id: UUID) -> ProfileOut:
        profile = await self._repo.get_by_auth_user_id(auth_user_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return ProfileOut.model_validate(profile)

    async def list(self, limit: int, offset: int) -> list[ProfileOut]:
        profiles = await self._repo.list_all(limit=limit, offset=offset)
        return [ProfileOut.model_validate(p) for p in profiles]

    async def update_full_name(
        self, auth_user_id: UUID, full_name: str | None
    ) -> ProfileOut:
        profile = await self._repo.update_full_name(auth_user_id, full_name)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return ProfileOut.model_validate(profile)

    async def update_role(self, auth_user_id: UUID, role: str) -> ProfileOut:
        profile = await self._repo.update_role(auth_user_id, role)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return ProfileOut.model_validate(profile)
