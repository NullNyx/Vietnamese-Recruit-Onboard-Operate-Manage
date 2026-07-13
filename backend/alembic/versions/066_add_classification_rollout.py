"""Add Organization classification rollout state and telemetry.

Revision ID: 066
Revises: 065
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "066"
down_revision: str | None = "065"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "classification_policy",
            sa.String(50),
            nullable=False,
            server_default="recall_first",
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "classification_policy_version",
            sa.String(100),
            nullable=False,
            server_default="recall-first-v1",
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "stable_classifier_version",
            sa.String(100),
            nullable=False,
            server_default="classifier-v1",
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column("candidate_classifier_version", sa.String(100), nullable=True),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column("candidate_classification_policy", sa.String(50), nullable=True),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column("candidate_classification_policy_version", sa.String(100), nullable=True),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column("rollout_mode", sa.String(20), nullable=False, server_default="stable"),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column("canary_percentage", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_org_ai_rollout_canary_percentage",
        "organization_ai_configurations",
        "canary_percentage >= 0 AND canary_percentage <= 100",
    )

    op.create_table(
        "classification_rollout_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("gmail_message_id", sa.String(255), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("selected_classifier_version", sa.String(100), nullable=False),
        sa.Column("stable_intent", sa.String(50), nullable=True),
        sa.Column("candidate_intent", sa.String(50), nullable=True),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("has_cv", sa.Boolean(), nullable=False),
        sa.Column("stable_latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidate_latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "candidate_provider_error",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_classification_rollout_events_gmail_message_id",
        "classification_rollout_events",
        ["gmail_message_id"],
    )
    op.create_index(
        "ix_classification_rollout_events_created_at",
        "classification_rollout_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_classification_rollout_events_created_at",
        table_name="classification_rollout_events",
    )
    op.drop_index(
        "ix_classification_rollout_events_gmail_message_id",
        table_name="classification_rollout_events",
    )
    op.drop_table("classification_rollout_events")
    op.drop_constraint(
        "ck_org_ai_rollout_canary_percentage",
        "organization_ai_configurations",
        type_="check",
    )
    for column in (
        "canary_percentage",
        "rollout_mode",
        "candidate_classification_policy_version",
        "candidate_classification_policy",
        "candidate_classifier_version",
        "stable_classifier_version",
        "classification_policy_version",
        "classification_policy",
    ):
        op.drop_column("organization_ai_configurations", column)
