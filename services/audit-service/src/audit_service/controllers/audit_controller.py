from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from ford_shared.security.dependencies import Principal
from ford_shared.security.rbac import Role, require_role
from slowapi import Limiter
from slowapi.util import get_remote_address

from audit_service.dependencies import get_audit_service
from audit_service.schemas import AuditEventOut
from audit_service.services import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/events",
    response_model=list[AuditEventOut],
    summary="List audit events (admin only)",
)
@limiter.limit("30/minute")
async def list_events(
    request: Request,
    event_type: str | None = Query(default=None, max_length=80),
    actor_user_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: Principal = Depends(require_role(Role.ADMIN)),
    service: AuditService = Depends(get_audit_service),
) -> list[AuditEventOut]:
    return await service.list_events(
        event_type=event_type,
        actor_user_id=actor_user_id,
        limit=limit,
        offset=offset,
    )
