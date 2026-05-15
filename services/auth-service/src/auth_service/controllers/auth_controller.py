"""HTTP layer for auth: register, login, refresh, me."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.dependencies import get_auth_service, get_db_session
from auth_service.repositories import UserRepository
from auth_service.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from auth_service.services import AuthService
from ford_shared.security.dependencies import Principal, get_current_principal

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (defaults to role=user)",
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    auth: AuthService = Depends(get_auth_service),
) -> UserOut:
    return await auth.register(payload)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Exchange credentials for an access + refresh token pair",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    auth: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await auth.login(payload.email, payload.password)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate refresh token and obtain a new access token",
)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    payload: RefreshRequest,
    auth: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await auth.refresh(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Return the caller's profile (requires Bearer access token)",
)
async def me(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> UserOut:
    user = await UserRepository(session).get_by_id(UUID(principal.user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)
