"""Add calendar_id column to calendar_sync_cursors for per-calendar sync.

Calendar sync tokens are scoped per calendar, so the cursor must track which
calendar the sync_token belongs to. This column replaces the singleton approach
with a composite (organization_singleton_key, calendar_id) unique constraint.

Revision ID: 073
Revises: 072
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "073"
down_revision: str | None = "072"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add calendar_id as nullable initially (existing rows get backfilled).
    op.add_column(
        "calendar_sync_cursors",
        sa.Column("calendar_id", sa.String(length=255), nullable=True),
    )

    # 2. Backfill existing rows with "primary" so the new NOT NULL constraint
    #    is satisfied for any cursors created before this migration.
    op.execute(
        "UPDATE calendar_sync_cursors SET calendar_id = 'primary' WHERE calendar_id IS NULL"
    )

    # 3. Now make it NOT NULL and add an index.
    op.alter_column(
        "calendar_sync_cursors",
        "calendar_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.create_index(
        "ix_calendar_sync_cursors_calendar_id",
        "calendar_sync_cursors",
        ["calendar_id"],
    )

    # 4. Drop the old singleton unique constraint on organization_singleton_key.
    op.drop_constraint(
        "calendar_sync_cursors_organization_singleton_key_key",
        "calendar_sync_cursors",
        type_="unique",
    )

    # 5. Create composite unique constraint.
    op.create_unique_constraint(
        "uq_org_calendar_sync_cursor",
        "calendar_sync_cursors",
        ["organization_singleton_key", "calendar_id"],
    )


def downgrade() -> None:
    # 1. Drop the composite unique constraint.
    op.drop_constraint(
        "uq_org_calendar_sync_cursor",
        "calendar_sync_cursors",
        type_="unique",
    )

    # 2. Re-create the old singleton unique constraint.
    op.create_unique_constraint(
        "calendar_sync_cursors_organization_singleton_key_key",
        "calendar_sync_cursors",
        ["organization_singleton_key"],
    )

    # 3. Drop the index and column.
    op.drop_index(
        "ix_calendar_sync_cursors_calendar_id",
        table_name="calendar_sync_cursors",
    )
    op.drop_column("calendar_sync_cursors", "calendar_id")
