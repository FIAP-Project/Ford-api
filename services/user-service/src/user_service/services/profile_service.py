from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from ford_shared.events import EventBus, EventType, RoleChangedEvent
from ford_shared.security.crypto import FieldCipher

from user_service.models import UserProfile
from user_service.repositories import ProfileRepository
from user_service.schemas import ProfileOut

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(
        self, repo: ProfileRepository, cipher: FieldCipher, event_bus: EventBus
    ) -> None:
        self._repo = repo
        self._cipher = cipher
        self._events = event_bus

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

    async def update_role(
        self, auth_user_id: UUID, role: str, *, actor_user_id: str
    ) -> ProfileOut:
        existing = await self._repo.get_by_auth_user_id(auth_user_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        previous_role = existing.role

        profile = await self._repo.update_role(auth_user_id, role)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )

        logger.warning(
            "user.role_changed",
            extra={
                "user_id": str(auth_user_id),
                "actor_user_id": actor_user_id,
                "previous_role": previous_role,
                "new_role": role,
            },
        )
        await self._events.publish(
            EventType.ROLE_CHANGED.value,
            RoleChangedEvent(
                event_id=str(uuid4()),
                event_type=EventType.ROLE_CHANGED,
                occurred_at=datetime.now(UTC),
                actor_user_id=actor_user_id,
                user_id=str(auth_user_id),
                previous_role=previous_role,
                new_role=role,
            ).model_dump(),
        )
        return self._to_out(profile)
