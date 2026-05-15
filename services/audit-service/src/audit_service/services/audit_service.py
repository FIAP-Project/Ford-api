from __future__ import annotations

from uuid import UUID

from audit_service.repositories import EventRepository
from audit_service.schemas import AuditEventOut


class AuditService:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def list_events(
        self,
        *,
        event_type: str | None,
        actor_user_id: UUID | None,
        limit: int,
        offset: int,
    ) -> list[AuditEventOut]:
        rows = await self._repo.list(
            event_type=event_type,
            actor_user_id=actor_user_id,
            limit=limit,
            offset=offset,
        )
        return [AuditEventOut.model_validate(r) for r in rows]
