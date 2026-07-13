"""Add candidate_id column to job_applications table (GH #186).

Promotion requires linking a JobApplication to exactly one Candidate.

Revision ID: 063
Revises: 062
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "063"
down_revision: str | None = "062"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_applications",
        sa.Column("candidate_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_job_applications_candidate_id",
        "job_applications",
        ["candidate_id"],
        unique=True,
    )
    op.create_foreign_key(
        "fk_job_applications_candidate_id",
        "job_applications",
        "candidates",
        ["candidate_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_job_applications_candidate_id",
        "job_applications",
        type_="foreignkey",
    )
    op.drop_index("ix_job_applications_candidate_id", table_name="job_applications")
    op.drop_column("job_applications", "candidate_id")
