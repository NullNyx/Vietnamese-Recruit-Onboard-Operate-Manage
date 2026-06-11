"""Add job_openings table.

Revision ID: 035
Revises: 034
Create Date: 2026-06-10
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create job_openings table."""
    op.create_table(
        "job_openings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=5000), nullable=False),
        sa.Column(
            "position_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("target_headcount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "closed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_openings_id", "job_openings", ["id"])
    op.create_index("ix_job_openings_title", "job_openings", ["title"])
    op.create_index("ix_job_openings_position_id", "job_openings", ["position_id"])
    op.create_index("ix_job_openings_status", "job_openings", ["status"])
    op.create_index(
        "ix_job_openings_created_at",
        "job_openings",
        ["created_at"],
    )
    op.create_foreign_key(
        "fk_job_openings_position_id",
        "job_openings",
        "positions",
        ["position_id"],
        ["id"],
    )

    # Add nullable FK from candidates to job_openings (Candidate assignment per ADR-0014).
    op.add_column(
        "candidates",
        sa.Column(
            "job_opening_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_candidates_job_opening_id",
        "candidates",
        ["job_opening_id"],
    )
    op.create_foreign_key(
        "fk_candidates_job_opening_id",
        "candidates",
        "job_openings",
        ["job_opening_id"],
        ["id"],
    )


def downgrade() -> None:
    """Drop job_openings table and FK from candidates."""
    op.drop_constraint(
        "fk_candidates_job_opening_id",
        table_name="candidates",
    )
    op.drop_index("ix_candidates_job_opening_id", table_name="candidates")
    op.drop_column("candidates", "job_opening_id")

    op.drop_constraint(
        "fk_job_openings_position_id",
        table_name="job_openings",
    )
    op.drop_index("ix_job_openings_created_at", table_name="job_openings")
    op.drop_index("ix_job_openings_status", table_name="job_openings")
    op.drop_index("ix_job_openings_position_id", table_name="job_openings")
    op.drop_index("ix_job_openings_title", table_name="job_openings")
    op.drop_index("ix_job_openings_id", table_name="job_openings")
    op.drop_table("job_openings")
