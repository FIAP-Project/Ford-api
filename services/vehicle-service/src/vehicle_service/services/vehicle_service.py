"""Orchestrates the vehicle-query use case end-to-end."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from ford_shared.events import (
    EventBus,
    EventType,
    VehicleQueryCompletedEvent,
    VehicleQueryRequestedEvent,
)
from vehicle_service.repositories import QueryRepository
from vehicle_service.schemas import QueryRequest, QueryResponse, QuerySummary, SpecOut
from vehicle_service.services.claude_client import ClaudeClient
from vehicle_service.services.specs_normalizer import normalize_specs

logger = logging.getLogger(__name__)


class VehicleService:
    def __init__(
        self,
        repo: QueryRepository,
        claude: ClaudeClient,
        event_bus: EventBus,
    ) -> None:
        self._repo = repo
        self._claude = claude
        self._events = event_bus

    async def query(self, user_id: UUID, payload: QueryRequest) -> QueryResponse:
        started = time.monotonic()
        query = await self._repo.create(
            user_id=user_id,
            brand=payload.brand,
            model=payload.model,
            version=payload.version,
            attributes=payload.attributes,
        )
        await self._publish_requested(query.id, user_id, payload)

        try:
            claude_result = await self._claude.fetch_vehicle_specs(
                brand=payload.brand,
                model=payload.model,
                version=payload.version,
                attributes=payload.attributes,
            )
        except Exception as exc:
            logger.exception("vehicle.query.claude_failed")
            await self._repo.mark_failed(query, str(exc))
            await self._publish_completed(
                query.id, user_id, "failed", 0, int((time.monotonic() - started) * 1000)
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Upstream specification provider failed",
            ) from exc

        normalized = normalize_specs(payload.attributes, claude_result.specs)
        await self._repo.attach_specs(query, normalized)
        await self._repo.mark_completed(query, claude_result.raw_response)
        await self._publish_completed(
            query.id,
            user_id,
            "completed",
            len(normalized),
            int((time.monotonic() - started) * 1000),
        )

        return QueryResponse(
            id=query.id,
            user_id=user_id,
            brand=query.brand,
            model=query.model,
            version=query.version,
            status=query.status,
            created_at=query.created_at,
            specs=[
                SpecOut(
                    attribute=s.attribute,
                    value=s.value,
                    available=s.available,
                    normalized_unit=s.normalized_unit,
                    source_hint=s.source_hint,
                )
                for s in normalized
            ],
        )

    async def get(
        self, query_id: UUID, *, requester_id: UUID, can_see_others: bool
    ) -> QueryResponse:
        query = await self._repo.get(query_id)
        if query is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
            )
        if not can_see_others and query.user_id != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to view this query",
            )
        return QueryResponse(
            id=query.id,
            user_id=query.user_id,
            brand=query.brand,
            model=query.model,
            version=query.version,
            status=query.status,
            created_at=query.created_at,
            specs=[SpecOut.model_validate(s) for s in query.specs],
        )

    async def history(
        self,
        *,
        requester_id: UUID,
        can_see_others: bool,
        limit: int,
        offset: int,
    ) -> list[QuerySummary]:
        rows = (
            await self._repo.list_all(limit, offset)
            if can_see_others
            else await self._repo.list_by_user(requester_id, limit, offset)
        )
        return [QuerySummary.model_validate(r) for r in rows]

    async def _publish_requested(
        self, query_id: UUID, user_id: UUID, payload: QueryRequest
    ) -> None:
        event = VehicleQueryRequestedEvent(
            event_id=str(uuid4()),
            event_type=EventType.VEHICLE_QUERY_REQUESTED,
            occurred_at=datetime.now(UTC),
            actor_user_id=str(user_id),
            query_id=str(query_id),
            user_id=str(user_id),
            brand=payload.brand,
            model=payload.model,
            version=payload.version,
            attributes=payload.attributes,
        )
        await self._events.publish(
            EventType.VEHICLE_QUERY_REQUESTED.value, event.model_dump()
        )

    async def _publish_completed(
        self,
        query_id: UUID,
        user_id: UUID,
        status: str,
        spec_count: int,
        duration_ms: int,
    ) -> None:
        event = VehicleQueryCompletedEvent(
            event_id=str(uuid4()),
            event_type=EventType.VEHICLE_QUERY_COMPLETED,
            occurred_at=datetime.now(UTC),
            actor_user_id=str(user_id),
            query_id=str(query_id),
            user_id=str(user_id),
            status=status,
            spec_count=spec_count,
            duration_ms=duration_ms,
        )
        await self._events.publish(
            EventType.VEHICLE_QUERY_COMPLETED.value, event.model_dump()
        )
