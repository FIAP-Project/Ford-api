from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ford_shared.security.dependencies import Principal, get_current_principal
from ford_shared.security.rbac import Role, require_role
from user_service.dependencies import get_profile_service
from user_service.schemas import ProfileOut, ProfileUpdate
from user_service.schemas.profile import RoleUpdate
from user_service.services import ProfileService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=ProfileOut,
    summary="Return the caller's profile",
)
async def me(
    principal: Principal = Depends(get_current_principal),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileOut:
    return await service.get(UUID(principal.user_id))


@router.patch(
    "/me",
    response_model=ProfileOut,
    summary="Update the caller's profile (full_name only)",
)
async def update_me(
    payload: ProfileUpdate,
    principal: Principal = Depends(get_current_principal),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileOut:
    return await service.update_full_name(UUID(principal.user_id), payload.full_name)


@router.get(
    "",
    response_model=list[ProfileOut],
    summary="List user profiles (analyst+)",
)
async def list_profiles(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: Principal = Depends(require_role(Role.ANALYST)),
    service: ProfileService = Depends(get_profile_service),
) -> list[ProfileOut]:
    return await service.list(limit=limit, offset=offset)


@router.put(
    "/{user_id}/role",
    response_model=ProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Change a user's role (admin-only)",
)
async def update_role(
    user_id: UUID,
    payload: RoleUpdate,
    _: Principal = Depends(require_role(Role.ADMIN)),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileOut:
    return await service.update_role(user_id, payload.role.value)
