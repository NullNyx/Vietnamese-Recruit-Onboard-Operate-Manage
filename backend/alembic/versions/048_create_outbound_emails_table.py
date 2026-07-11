"""Create outbound_emails table.

Revision ID: 048
Revises: fe0a86a67893
Create Date: 2026-07-11 12:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "048"
down_revision: Union[str, None] = "fe0a86a67893"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outbound_emails",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=True),
        sa.Column("subject", sa.String(length=998), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("sender_email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("gmail_message_id", sa.String(length=255), nullable=True),
        sa.Column("gmail_thread_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["candidate_id"], ["recruitment_candidates.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("idempotency_key", name="uq_outbound_emails_idempotency_key"),
    )
    op.create_index(op.f("ix_outbound_emails_idempotency_key"), "outbound_emails", ["idempotency_key"], unique=True)
    op.create_index(op.f("ix_outbound_emails_status"), "outbound_emails", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_outbound_emails_status"), table_name="outbound_emails")
    op.drop_index(op.f("ix_outbound_emails_idempotency_key"), table_name="outbound_emails")
    op.drop_table("outbound_emails")
