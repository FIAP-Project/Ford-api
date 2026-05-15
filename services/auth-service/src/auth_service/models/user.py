"""User model — owns identity and credentials."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from ford_shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
