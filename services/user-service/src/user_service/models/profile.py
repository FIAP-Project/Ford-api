from __future__ import annotations

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ford_shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = {"schema": "users"}

    auth_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(CITEXT, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
