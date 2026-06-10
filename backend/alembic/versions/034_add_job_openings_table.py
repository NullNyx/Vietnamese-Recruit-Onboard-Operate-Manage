"""Add job_openings table.

Revision ID: 034
Revises: 033
Create Date: 2026-06-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "034"
down_revision = "033"
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
            sa.ForeignKey("positions.id"),
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


def downgrade() -> None:
    """Drop job_openings table."""
    op.drop_index("ix_job_openings_created_at", table_name="job_openings")
    op.drop_index("ix_job_openings_status", table_name="job_openings")
    op.drop_index("ix_job_openings_position_id", table_name="job_openings")
    op.drop_index("ix_job_openings_title", table_name="job_openings")
    op.drop_index("ix_job_openings_id", table_name="job_openings")
    op.drop_table("job_openings")
