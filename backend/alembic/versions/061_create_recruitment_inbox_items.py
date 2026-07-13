"""Create recruitment_inbox_items table.

Creates the ``recruitment_inbox_items`` table for emails below confidence
threshold (needs_classification) and exhausted-provider retries.
Inbox state lives only on RecruitmentInboxItem, not on JobApplication.

GH #184 — Recruitment Inbox

Revision ID: 061
Revises: 060
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "061"
down_revision: str | None = "060"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # Create recruitment_inbox_items table                               #
    # ------------------------------------------------------------------ #
    op.create_table(
        "recruitment_inbox_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_email_message_id", sa.Uuid(), nullable=False),
        sa.Column("gmail_message_id", sa.String(255), nullable=False),
        sa.Column("gmail_thread_id", sa.String(255), nullable=False),
        sa.Column("sender_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("sender_email", sa.String(255), nullable=False, server_default=""),
        sa.Column("subject", sa.String(500), nullable=False, server_default=""),
        sa.Column("snippet", sa.String(2000), nullable=False, server_default=""),
        sa.Column("has_attachments", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # Safe attachment metadata (JSON: count, names, types, sizes)
        sa.Column("attachments_metadata", sa.JSON(), nullable=True),
        # Classification result
        sa.Column(
            "inbox_status",
            sa.String(30),
            nullable=False,
            server_default="needs_classification",
        ),
        sa.Column("prediction_intent", sa.String(50), nullable=True),
        sa.Column("confidence_raw", sa.Float(), nullable=True),
        sa.Column("confidence_calibrated", sa.Float(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("source_hints", sa.JSON(), nullable=True),
        # Correction tracking
        sa.Column("corrected_intent", sa.String(50), nullable=True),
        sa.Column("corrected_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correction_history", sa.JSON(), nullable=True),
        # Dismissal
        sa.Column("dismissed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_by_user_id", sa.Uuid(), nullable=True),
        # Retry tracking
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "is_retry_exhausted", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("processing_error", sa.String(500), nullable=True),
        # Timestamps
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
            name="fk_recruitment_inbox_items_source_email_message_id",
        ),
        sa.ForeignKeyConstraint(
            ["corrected_by_user_id"],
            ["users.id"],
            name="fk_recruitment_inbox_items_corrected_by_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["dismissed_by_user_id"],
            ["users.id"],
            name="fk_recruitment_inbox_items_dismissed_by_user_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recruitment_inbox_items_gmail_message_id",
        "recruitment_inbox_items",
        ["gmail_message_id"],
        unique=True,
    )
    op.create_index(
        "ix_recruitment_inbox_items_inbox_status",
        "recruitment_inbox_items",
        ["inbox_status"],
    )
    op.create_index(
        "ix_recruitment_inbox_items_dismissed",
        "recruitment_inbox_items",
        ["dismissed"],
    )
    op.create_index(
        "ix_recruitment_inbox_items_source_email_message_id",
        "recruitment_inbox_items",
        ["source_email_message_id"],
    )


def downgrade() -> None:
    # Drop recruitment_inbox_items table
    op.drop_index(
        "ix_recruitment_inbox_items_source_email_message_id",
        table_name="recruitment_inbox_items",
    )
    op.drop_index(
        "ix_recruitment_inbox_items_dismissed",
        table_name="recruitment_inbox_items",
    )
    op.drop_index(
        "ix_recruitment_inbox_items_inbox_status",
        table_name="recruitment_inbox_items",
    )
    op.drop_index(
        "ix_recruitment_inbox_items_gmail_message_id",
        table_name="recruitment_inbox_items",
    )
    op.drop_constraint(
        "fk_recruitment_inbox_items_dismissed_by_user_id",
        "recruitment_inbox_items",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_recruitment_inbox_items_corrected_by_user_id",
        "recruitment_inbox_items",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_recruitment_inbox_items_source_email_message_id",
        "recruitment_inbox_items",
        type_="foreignkey",
    )
    op.drop_table("recruitment_inbox_items")
