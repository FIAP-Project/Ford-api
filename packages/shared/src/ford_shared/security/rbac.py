"""Role-Based Access Control primitives."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum

from fastapi import Depends, HTTPException, status


class Role(StrEnum):
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"


_HIERARCHY = {Role.USER: 0, Role.ANALYST: 1, Role.ADMIN: 2}


def role_at_least(actual: Role, required: Role) -> bool:
    return _HIERARCHY[actual] >= _HIERARCHY[required]


def require_role(required: Role) -> Callable:
    """FastAPI dependency factory that enforces a minimum role.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(Role.ADMIN))])
    """

    from ford_shared.security.dependencies import get_current_principal

    def _checker(principal=Depends(get_current_principal)):
        if not role_at_least(principal.role, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges",
            )
        return principal

    return _checker
