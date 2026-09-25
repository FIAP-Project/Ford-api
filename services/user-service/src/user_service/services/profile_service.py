from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from ford_shared.security.crypto import FieldCipher

from user_service.models import UserProfile
from user_service.repositories import ProfileRepository
from user_service.schemas import ProfileOut


class ProfileService:
    def __init__(self, repo: ProfileRepository, cipher: FieldCipher) -> None:
        self._repo = repo
        self._cipher = cipher

    def _to_out(self, profile: UserProfile) -> ProfileOut:
        return ProfileOut(
            id=profile.id,
            auth_user_id=profile.auth_user_id,
            email=profile.email,
            role=profile.role,
            full_name=self._cipher.decrypt(profile.full_name),
        )

    async def get(self, auth_user_id: UUID) -> ProfileOut:
        profile = await self._repo.get_by_auth_user_id(auth_user_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return self._to_out(profile)

    async def list(self, limit: int, offset: int) -> list[ProfileOut]:
        profiles = await self._repo.list_all(limit=limit, offset=offset)
        return [self._to_out(p) for p in profiles]

    async def update_full_name(
        self, auth_user_id: UUID, full_name: str | None
    ) -> ProfileOut:
        profile = await self._repo.update_full_name(
            auth_user_id, self._cipher.encrypt(full_name)
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return self._to_out(profile)

    async def update_role(self, auth_user_id: UUID, role: str) -> ProfileOut:
        profile = await self._repo.update_role(auth_user_id, role)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return self._to_out(profile)
