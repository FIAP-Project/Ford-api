from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from audit_service.repositories import EventRepository
from audit_service.services import AuditService
from ford_shared.db import Database


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db: Database = request.app.state.database
    async for session in db.session():
        yield session


def get_audit_service(session: AsyncSession = Depends(get_db_session)) -> AuditService:
    return AuditService(EventRepository(session))
