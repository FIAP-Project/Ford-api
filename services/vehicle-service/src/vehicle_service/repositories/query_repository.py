from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from vehicle_service.models import VehicleQuery, VehicleSpec

if TYPE_CHECKING:
    from vehicle_service.services.claude_client import ClaudeSpec


class QueryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        brand: str,
        model: str,
        version: str,
        attributes: list[str],
    ) -> VehicleQuery:
        query = VehicleQuery(
            user_id=user_id,
            brand=brand,
            model=model,
            version=version,
            requested_attrs=attributes,
            status="pending",
        )
        self._session.add(query)
        await self._session.flush()
        return query

    async def attach_specs(
        self, query: VehicleQuery, specs: Sequence[ClaudeSpec]
    ) -> None:
        for spec in specs:
            self._session.add(
                VehicleSpec(
                    query_id=query.id,
                    attribute=spec.attribute,
                    value=spec.value,
                    available=spec.available,
                    normalized_unit=spec.normalized_unit,
                    source_hint=spec.source_hint,
                )
            )
        await self._session.flush()

    async def mark_completed(
        self, query: VehicleQuery, raw_response: dict[str, Any]
    ) -> None:
        query.status = "completed"
        query.raw_response = raw_response
        await self._session.flush()

    async def mark_failed(self, query: VehicleQuery, error: str) -> None:
        query.status = "failed"
        query.error_message = error[:500]
        await self._session.flush()

    async def get(self, query_id: UUID) -> VehicleQuery | None:
        return await self._session.get(VehicleQuery, query_id)

    async def list_by_user(
        self, user_id: UUID, limit: int, offset: int
    ) -> Sequence[VehicleQuery]:
        result = await self._session.execute(
            select(VehicleQuery)
            .where(VehicleQuery.user_id == user_id)
            .order_by(VehicleQuery.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def list_all(self, limit: int, offset: int) -> Sequence[VehicleQuery]:
        result = await self._session.execute(
            select(VehicleQuery)
            .order_by(VehicleQuery.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
