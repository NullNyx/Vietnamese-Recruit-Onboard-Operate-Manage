"""Create correction_records, evaluation_sets, and evaluation_samples tables (GH #187).

Captures safe classification evaluation feedback: correction records for HR
decisions without raw content, and redacted evaluation samples for versioned
evaluation sets.

Revision ID: 064
Revises: 063
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "064"
down_revision: str | None = "063"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- correction_records ---
    op.create_table(
        "correction_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        # Prediction
        sa.Column("prediction_intent", sa.String(50), nullable=True),
        sa.Column("confidence_raw", sa.Float(), nullable=True),
        sa.Column("confidence_calibrated", sa.Float(), nullable=True),
        # HR correction
        sa.Column("corrected_intent", sa.String(50), nullable=False),
        sa.Column("previous_inbox_status", sa.String(30), nullable=True),
        # Who and when
        sa.Column("corrected_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
        # Versions
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(100), nullable=True),
        sa.Column("policy_version", sa.String(100), nullable=True),
        # Safe evidence
        sa.Column("evidence", JSONB(), nullable=True),
        sa.Column("source_hints", JSONB(), nullable=True),
        # Evaluation opt-in
        sa.Column("evaluation_status", sa.String(20), nullable=False, server_default="none"),
        # Guard
        sa.Column(
            "triggers_online_learning",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        # Redacted fields
        sa.Column("redacted_subject", sa.String(500), nullable=True),
        sa.Column("redacted_snippet", sa.String(2000), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_correction_records_source_id",
        "correction_records",
        ["source_id"],
    )

    # --- evaluation_sets ---
    op.create_table(
        "evaluation_sets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(30), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_sets_version", "evaluation_sets", ["version"])

    # --- evaluation_samples ---
    op.create_table(
        "evaluation_samples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "correction_record_id",
            sa.Uuid(),
            sa.ForeignKey("correction_records.id"),
            nullable=False,
        ),
        sa.Column(
            "evaluation_set_id",
            sa.Uuid(),
            sa.ForeignKey("evaluation_sets.id"),
            nullable=False,
        ),
        # Redacted content
        sa.Column("redacted_subject", sa.String(500), nullable=False, server_default=""),
        sa.Column("redacted_snippet", sa.String(2000), nullable=False, server_default=""),
        sa.Column("redacted_sender_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("redacted_sender_email", sa.String(255), nullable=False, server_default=""),
        # Ground truth
        sa.Column("ground_truth_intent", sa.String(50), nullable=False),
        # Versions
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(100), nullable=True),
        sa.Column("policy_version", sa.String(100), nullable=True),
        # Cohorts
        sa.Column("cohorts", JSONB(), nullable=False, server_default="[]"),
        # Timestamps
        sa.Column("redacted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evaluation_samples_correction_record_id",
        "evaluation_samples",
        ["correction_record_id"],
    )
    op.create_index(
        "ix_evaluation_samples_evaluation_set_id",
        "evaluation_samples",
        ["evaluation_set_id"],
    )


def downgrade() -> None:
    op.drop_table("evaluation_samples")
    op.drop_table("evaluation_sets")
    op.drop_table("correction_records")
