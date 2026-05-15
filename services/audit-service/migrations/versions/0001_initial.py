"""Initial audit schema: events.

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
    op.execute('CREATE SCHEMA IF NOT EXISTS audit')

    op.create_table(
        "events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("routing_key", sa.String(120), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature", sa.String(128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="audit",
    )
    op.create_index("ix_audit_events_event_type", "events", ["event_type"], schema="audit")
    op.create_index("ix_audit_events_routing_key", "events", ["routing_key"], schema="audit")
    op.create_index("ix_audit_events_actor_user_id", "events", ["actor_user_id"], schema="audit")
    op.create_index("ix_audit_events_occurred_at", "events", ["occurred_at"], schema="audit")


def downgrade() -> None:
    op.drop_table("events", schema="audit")
