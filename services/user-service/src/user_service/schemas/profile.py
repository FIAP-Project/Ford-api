from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ford_shared.security.rbac import Role


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auth_user_id: UUID
    email: EmailStr
    role: Role
    full_name: str | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str | None = Field(default=None, max_length=120, pattern=r"^[\w\s\-\.']+$")


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role
