from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ford_shared.db import Database
from ford_shared.events import EventBus
from vehicle_service.repositories.query_repository import QueryRepository
from vehicle_service.services.claude_client import ClaudeClient
from vehicle_service.services.vehicle_service import VehicleService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db: Database = request.app.state.database
    async for session in db.session():
        yield session


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus


def get_claude(request: Request) -> ClaudeClient:
    return request.app.state.claude_client


def get_vehicle_service(
    session: AsyncSession = Depends(get_db_session),
    bus: EventBus = Depends(get_event_bus),
    claude: ClaudeClient = Depends(get_claude),
) -> VehicleService:
    return VehicleService(
        repo=QueryRepository(session), claude=claude, event_bus=bus
    )
