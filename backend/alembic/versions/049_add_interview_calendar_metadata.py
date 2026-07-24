"""Add calendar_etag, calendar_updated, meeting_mode, meeting_link to interviews
and response_status to interview_participants.

Revision ID: 049
Revises: 048
Create Date: 2026-07-11 16:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "049"
down_revision: str | None = "048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add fields to interviews table
    op.add_column(
        "interviews",
        sa.Column("calendar_etag", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "interviews",
        sa.Column("calendar_updated", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "interviews",
        sa.Column(
            "meeting_mode", sa.String(length=20), nullable=False, server_default="google_meet"
        ),
    )
    op.add_column(
        "interviews",
        sa.Column("meeting_link", sa.String(length=1024), nullable=True),
    )

    # Add response_status to interview_participants
    op.add_column(
        "interview_participants",
        sa.Column("response_status", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interview_participants", "response_status")
    op.drop_column("interviews", "meeting_link")
    op.drop_column("interviews", "meeting_mode")
    op.drop_column("interviews", "calendar_updated")
    op.drop_column("interviews", "calendar_etag")
