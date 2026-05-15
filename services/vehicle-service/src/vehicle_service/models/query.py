from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ford_shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VehicleQuery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "queries"
    __table_args__ = {"schema": "vehicle"}

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(120), nullable=False)
    requested_attrs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    specs: Mapped[list["VehicleSpec"]] = relationship(
        "VehicleSpec",
        back_populates="query",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


from vehicle_service.models.spec import VehicleSpec  # noqa: E402
