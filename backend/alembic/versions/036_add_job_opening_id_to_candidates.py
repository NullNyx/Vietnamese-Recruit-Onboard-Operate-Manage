"""Add job_opening_id FK to candidates table.

Revision ID: 036
Revises: 035
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable job_opening_id FK to candidates."""
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
    """Remove job_opening_id column from candidates."""
    op.drop_constraint(
        "fk_candidates_job_opening_id",
        table_name="candidates",
    )
    op.drop_index("ix_candidates_job_opening_id", table_name="candidates")
    op.drop_column("candidates", "job_opening_id")
