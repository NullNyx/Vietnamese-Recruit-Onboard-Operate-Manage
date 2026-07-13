"""Add the stable Job Application intent and CV presence contract.

Revision ID: 068
Revises: 067
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "068"
down_revision: str | None = "067"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_applications",
        sa.Column("intent", sa.String(50), nullable=False, server_default="job_application"),
    )
    op.add_column(
        "job_applications",
        sa.Column("has_cv", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Legacy ``cv`` rows are applications with a CV; preserve the old email
    # category while making the new contract explicit and queryable.
    op.execute(
        sa.text(
            """
            UPDATE job_applications AS application
            SET intent = 'job_application',
                has_cv = COALESCE(email.has_attachments, FALSE)
            FROM email_messages AS email
            WHERE email.id = application.source_email_message_id
            """
        )
    )
    op.alter_column("job_applications", "intent", server_default=None)
    op.alter_column("job_applications", "has_cv", server_default=None)


def downgrade() -> None:
    op.drop_column("job_applications", "has_cv")
    op.drop_column("job_applications", "intent")
