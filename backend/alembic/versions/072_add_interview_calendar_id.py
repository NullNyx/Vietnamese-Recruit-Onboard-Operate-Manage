"""Add calendar_id column to interviews table.

Revision ID: 072
Revises: 071
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "072"
down_revision: str | None = "071"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add calendar_id column to interviews table."""
    op.add_column(
        "interviews",
        sa.Column("calendar_id", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    """Drop calendar_id column from interviews table."""
    op.drop_column("interviews", "calendar_id")
