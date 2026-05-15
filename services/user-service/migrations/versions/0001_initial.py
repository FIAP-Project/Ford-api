"""Initial users schema: user_profiles.

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
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute('CREATE SCHEMA IF NOT EXISTS users')

    op.create_table(
        "user_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("auth_user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("full_name", sa.String(120), nullable=True),
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
        schema="users",
    )
    op.create_index("ix_users_user_profiles_auth_user_id", "user_profiles", ["auth_user_id"], schema="users")
    op.create_index("ix_users_user_profiles_email", "user_profiles", ["email"], schema="users")


def downgrade() -> None:
    op.drop_table("user_profiles", schema="users")
