"""Widen full_name to hold encrypted (Fernet) ciphertext.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-25 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "user_profiles",
        "full_name",
        existing_type=sa.String(120),
        type_=sa.Text(),
        schema="users",
    )


def downgrade() -> None:
    op.alter_column(
        "user_profiles",
        "full_name",
        existing_type=sa.Text(),
        type_=sa.String(120),
        schema="users",
    )
