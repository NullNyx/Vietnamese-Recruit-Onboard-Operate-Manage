"""Persist AI Automation recovery metadata.

Revision ID: 059
Revises: 058
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "059"
down_revision: str | None = "058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("email_messages", sa.Column("processing_error", sa.String(500), nullable=True))
    op.add_column(
        "email_messages",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "email_messages",
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cv_documents",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cv_documents",
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cv_documents", "last_retry_at")
    op.drop_column("cv_documents", "next_retry_at")
    op.drop_column("email_messages", "last_retry_at")
    op.drop_column("email_messages", "next_retry_at")
    op.drop_column("email_messages", "processing_error")
