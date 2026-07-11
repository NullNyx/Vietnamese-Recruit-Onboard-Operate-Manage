"""Create calendar_sync_cursors table for calendar sync tracking.

Revision ID: 050
Revises: 049
Create Date: 2026-07-11 17:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "050"
down_revision: Union[str, None] = "049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_sync_cursors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "organization_singleton_key",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("sync_token", sa.String(length=1024), nullable=True),
        sa.Column("page_token", sa.String(length=1024), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_singleton_key"),
    )


def downgrade() -> None:
    op.drop_table("calendar_sync_cursors")
