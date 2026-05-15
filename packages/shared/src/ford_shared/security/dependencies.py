"""FastAPI dependencies for authentication."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ford_shared.security.jwt import InvalidTokenError, JWTService
from ford_shared.security.rbac import Role

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str
    role: Role
    jti: str


def get_jwt_service(request: Request) -> JWTService:
    service = getattr(request.app.state, "jwt_service", None)
    if service is None:
        raise RuntimeError("JWTService not configured on app.state")
    return service


def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt_service.decode(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return Principal(
        user_id=payload.sub,
        email=payload.email,
        role=payload.role,
        jti=payload.jti,
    )
