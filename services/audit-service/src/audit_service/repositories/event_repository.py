from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audit_service.models import AuditEvent


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        event_type: str,
        routing_key: str,
        actor_user_id: UUID | None,
        payload: dict[str, Any],
        occurred_at: datetime,
        signature: str,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            routing_key=routing_key,
            actor_user_id=actor_user_id,
            payload=payload,
            occurred_at=occurred_at,
            signature=signature,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list(
        self,
        *,
        event_type: str | None = None,
        actor_user_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditEvent]:
        stmt = select(AuditEvent).order_by(AuditEvent.occurred_at.desc())
        if event_type:
            stmt = stmt.where(AuditEvent.event_type == event_type)
        if actor_user_id:
            stmt = stmt.where(AuditEvent.actor_user_id == actor_user_id)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()
