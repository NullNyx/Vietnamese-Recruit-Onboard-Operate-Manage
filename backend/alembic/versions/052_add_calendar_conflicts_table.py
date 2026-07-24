"""Add calendar_conflicts table for calendar event write conflict resolution.

When a conditional write (If-Match) to Google Calendar fails with 412, the
CalendarConflict entity captures the local (Vroom-side) Interview state and
the remote (Google Calendar) event state without mutating the Interview or
Candidate. The conflict can later be resolved by an HR user (keep Google or
overwrite Vroom), with the actor/choice/timestamp audited.

Revision ID: 052
Revises: 051
Create Date: 2026-07-11 18:30:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "052"
down_revision: str | None = "051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calendar_conflicts",
        sa.Column("id", UUID, nullable=False),
        sa.Column("interview_id", UUID, nullable=False),
        sa.Column("candidate_id", UUID, nullable=False),
        sa.Column("calendar_event_id", sa.String(length=1024), nullable=False),
        sa.Column("local_snapshot", JSONB, nullable=False, server_default="{}"),
        sa.Column("remote_snapshot", JSONB, nullable=False, server_default="{}"),
        sa.Column("conflict_details", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="unresolved",
        ),
        sa.Column("resolved_by", UUID, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True, default=None),
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
        sa.ForeignKeyConstraint(
            ["interview_id"],
            ["interviews.id"],
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_calendar_conflicts_status",
        "calendar_conflicts",
        ["status"],
    )
    op.create_index(
        "ix_calendar_conflicts_interview_id",
        "calendar_conflicts",
        ["interview_id"],
    )
    op.create_index(
        "ix_calendar_conflicts_candidate_id",
        "calendar_conflicts",
        ["candidate_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_calendar_conflicts_status", table_name="calendar_conflicts")
    op.drop_index("ix_calendar_conflicts_interview_id", table_name="calendar_conflicts")
    op.drop_index("ix_calendar_conflicts_candidate_id", table_name="calendar_conflicts")
    op.drop_table("calendar_conflicts")
