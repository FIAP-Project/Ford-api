"""Pydantic schemas for /auth endpoints.

Notes on validation:
- Email validated via pydantic's EmailStr (RFC-compliant).
- Password requires min 12 chars, at least one upper, one lower, one digit, one symbol.
- All free-text inputs have max_length to prevent payload flooding.
"""

from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from ford_shared.security.rbac import Role

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{12,128}$"
)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=120, pattern=r"^[\w\s\-\.']+$")

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if not _PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Password must include upper, lower, digit, symbol and be 12-128 chars"
            )
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., min_length=10, max_length=2048)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds for access token


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: Role
    full_name: str | None = None
