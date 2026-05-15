from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from ford_shared.security.dependencies import Principal, get_current_principal
from ford_shared.security.rbac import Role, role_at_least
from vehicle_service.dependencies import get_vehicle_service
from vehicle_service.schemas import QueryRequest, QueryResponse, QuerySummary
from vehicle_service.services import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query technical specifications for a vehicle (brand/model/version)",
    description=(
        "Submits a vehicle to the AI-backed spec extractor and returns a standardized "
        "list of attributes. Missing attributes are returned with `available=false` "
        "so the response shape is always consistent."
    ),
)
@limiter.limit("20/minute")
async def query_vehicle(
    request: Request,
    payload: QueryRequest,
    principal: Principal = Depends(get_current_principal),
    service: VehicleService = Depends(get_vehicle_service),
) -> QueryResponse:
    return await service.query(UUID(principal.user_id), payload)


@router.get(
    "/queries",
    response_model=list[QuerySummary],
    summary="List previous queries (user: own; analyst+: all)",
)
async def list_queries(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    service: VehicleService = Depends(get_vehicle_service),
) -> list[QuerySummary]:
    can_see_others = role_at_least(principal.role, Role.ANALYST)
    return await service.history(
        requester_id=UUID(principal.user_id),
        can_see_others=can_see_others,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/queries/{query_id}",
    response_model=QueryResponse,
    summary="Get a specific query by id",
)
async def get_query(
    query_id: UUID,
    principal: Principal = Depends(get_current_principal),
    service: VehicleService = Depends(get_vehicle_service),
) -> QueryResponse:
    can_see_others = role_at_least(principal.role, Role.ANALYST)
    return await service.get(
        query_id,
        requester_id=UUID(principal.user_id),
        can_see_others=can_see_others,
    )
