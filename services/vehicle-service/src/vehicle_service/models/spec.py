from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ford_shared.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VehicleSpec(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "specs"
    __table_args__ = {"schema": "vehicle"}

    query_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle.queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    normalized_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_hint: Mapped[str | None] = mapped_column(String(200), nullable=True)

    query: Mapped["VehicleQuery"] = relationship(  # type: ignore[name-defined]
        "VehicleQuery", back_populates="specs"
    )
