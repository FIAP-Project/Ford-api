"""Initial vehicle schema: queries + specs.

Revision ID: 0001
Revises:
Create Date: 2026-05-15 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE SCHEMA IF NOT EXISTS vehicle')

    op.create_table(
        "queries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand", sa.String(80), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("version", sa.String(120), nullable=False),
        sa.Column(
            "requested_attrs",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("raw_response", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="vehicle",
    )
    op.create_index("ix_vehicle_queries_user_id", "queries", ["user_id"], schema="vehicle")

    op.create_table(
        "specs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("query_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attribute", sa.String(120), nullable=False),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("available", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("normalized_unit", sa.String(40), nullable=True),
        sa.Column("source_hint", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["query_id"], ["vehicle.queries.id"], ondelete="CASCADE"),
        schema="vehicle",
    )
    op.create_index("ix_vehicle_specs_query_id", "specs", ["query_id"], schema="vehicle")


def downgrade() -> None:
    op.drop_table("specs", schema="vehicle")
    op.drop_table("queries", schema="vehicle")
