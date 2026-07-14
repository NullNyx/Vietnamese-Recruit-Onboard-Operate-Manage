"""Move Gmail sync cursor ownership to the Organization singleton.

Revision ID: 071
Revises: 070
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "071"
down_revision: str | None = "070"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Collapse legacy per-user cursors into one Organization cursor."""
    op.add_column(
        "sync_cursors",
        sa.Column("organization_singleton_key", sa.String(length=32), nullable=True),
    )

    # Keep the most recently advanced cursor; all legacy rows represent the
    # same mailbox after the Organization ownership cutover.
    op.execute(
        sa.text(
            """
            DELETE FROM sync_cursors
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                           row_number() OVER (
                               ORDER BY last_poll_at DESC, id DESC
                           ) AS row_number
                    FROM sync_cursors
                ) ranked
                WHERE ranked.row_number > 1
            )
            """
        )
    )
    op.execute(sa.text("UPDATE sync_cursors SET organization_singleton_key = 'default'"))
    op.alter_column("sync_cursors", "organization_singleton_key", nullable=False)
    op.drop_constraint("sync_cursors_user_id_fkey", "sync_cursors", type_="foreignkey")
    op.drop_constraint("sync_cursors_user_id_key", "sync_cursors", type_="unique")
    op.drop_column("sync_cursors", "user_id")
    op.create_unique_constraint(
        "uq_sync_cursors_organization_singleton_key",
        "sync_cursors",
        ["organization_singleton_key"],
    )


def downgrade() -> None:
    """Restore the legacy cursor column shape for rollback compatibility."""
    # The Organization cursor has no safe HR owner to restore. Drop the
    # singleton row during rollback so the legacy NOT NULL invariant remains
    # valid and the pre-071 application can create a fresh cursor.
    op.add_column("sync_cursors", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.execute(sa.text("DELETE FROM sync_cursors"))
    op.alter_column("sync_cursors", "user_id", nullable=False)
    op.drop_constraint(
        "uq_sync_cursors_organization_singleton_key",
        "sync_cursors",
        type_="unique",
    )
    op.drop_column("sync_cursors", "organization_singleton_key")
    op.create_foreign_key("sync_cursors_user_id_fkey", "sync_cursors", "users", ["user_id"], ["id"])
    op.create_unique_constraint("sync_cursors_user_id_key", "sync_cursors", ["user_id"])
