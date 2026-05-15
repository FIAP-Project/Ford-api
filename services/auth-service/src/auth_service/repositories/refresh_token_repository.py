"""Persistence for refresh-token state — rotation + revocation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, user_id: UUID, jti: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_active(self, jti: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti,
                RefreshToken.revoked.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, jti: str) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(revoked=True)
        )
