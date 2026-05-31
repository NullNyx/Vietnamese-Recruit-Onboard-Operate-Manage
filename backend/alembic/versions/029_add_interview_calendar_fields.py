"""Add interview calendar fields and organization settings.

Realizes ADR-0008 (synchronous calendar interview scheduling) at the schema
level:

* Adds three nullable columns to the existing ``candidates`` table so a
  Candidate can carry its single interview's Google Calendar reference and
  time without a separate interview entity:
  ``calendar_event_id``, ``interview_start_at``, ``interview_timezone``.
* Adds a partial unique index on ``calendar_event_id`` (where not null) so the
  same Google Calendar event can never be attached to two Candidates — the
  "at most one calendar_event_id per Candidate" invariant.
* Creates the single-row ``organization_settings`` table holding the canonical
  IANA timezone used to interpret and render interview times.

Revision ID: 029
Revises: 028
Create Date: 2026-05-29
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "029"
down_revision: str | None = "028"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add interview columns + index to candidates and create org settings."""

    # --- candidates: interview calendar columns (R4.1, R4.2, R4.3) ---
    op.add_column(
        "candidates",
        sa.Column("calendar_event_id", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column("interview_start_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column("interview_timezone", sa.String(length=64), nullable=True),
    )

    # Partial unique index: enforces "at most one calendar_event_id per
    # Candidate" across rows (R4.4). Matches the entity-declared index.
    op.create_index(
        "ix_candidates_calendar_event_id",
        "candidates",
        ["calendar_event_id"],
        unique=True,
        postgresql_where=sa.text("calendar_event_id IS NOT NULL"),
    )

    # --- organization_settings: single-row timezone source of truth (R11.1) ---
    op.create_table(
        "organization_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default="Asia/Ho_Chi_Minh",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop org settings, the partial index, and the interview columns."""
    op.drop_table("organization_settings")

    op.drop_index("ix_candidates_calendar_event_id", table_name="candidates")

    op.drop_column("candidates", "interview_timezone")
    op.drop_column("candidates", "interview_start_at")
    op.drop_column("candidates", "calendar_event_id")
