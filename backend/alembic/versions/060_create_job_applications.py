"""Create job_applications table for Job Application ingestion.

Revision ID: 060
Revises: 059
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "060"
down_revision: str | None = "059"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_email_message_id", sa.Uuid(), nullable=False),
        sa.Column("gmail_message_id", sa.String(255), nullable=False),
        sa.Column("gmail_thread_id", sa.String(255), nullable=False),
        sa.Column("source", sa.String(30), nullable=False, server_default="direct"),
        sa.Column("applicant_name", sa.String(255), nullable=True),
        sa.Column("applicant_email", sa.String(255), nullable=True),
        sa.Column("sender_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("sender_email", sa.String(255), nullable=False, server_default=""),
        sa.Column("job_opening_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
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
            ["source_email_message_id"],
            ["email_messages.id"],
            name="fk_job_applications_source_email_message_id",
        ),
        sa.ForeignKeyConstraint(
            ["job_opening_id"],
            ["job_openings.id"],
            name="fk_job_applications_job_opening_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_job_applications_source_email_message_id",
        "job_applications",
        ["source_email_message_id"],
    )
    op.create_index(
        "ix_job_applications_gmail_message_id",
        "job_applications",
        ["gmail_message_id"],
        unique=True,
    )
    op.create_index(
        "ix_job_applications_job_opening_id",
        "job_applications",
        ["job_opening_id"],
    )
    op.create_index(
        "ix_job_applications_status",
        "job_applications",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_applications_status", table_name="job_applications")
    op.drop_index("ix_job_applications_job_opening_id", table_name="job_applications")
    op.drop_index("ix_job_applications_gmail_message_id", table_name="job_applications")
    op.drop_index(
        "ix_job_applications_source_email_message_id",
        table_name="job_applications",
    )
    op.drop_constraint(
        "fk_job_applications_job_opening_id",
        "job_applications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_job_applications_source_email_message_id",
        "job_applications",
        type_="foreignkey",
    )
    op.drop_table("job_applications")
