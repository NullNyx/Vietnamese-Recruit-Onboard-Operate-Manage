"""Add reproducibility and cost metadata to classification telemetry.

Revision ID: 067
Revises: 066
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "067"
down_revision: str | None = "066"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "classification_rollout_events",
        sa.Column("prompt_version", sa.String(100), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "classification_rollout_events",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "classification_rollout_events",
        sa.Column("retry_failure", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "classification_rollout_events",
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "classification_rollout_events",
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "classification_rollout_events",
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    for column in (
        "estimated_cost_usd",
        "completion_tokens",
        "prompt_tokens",
        "retry_failure",
        "retry_count",
        "prompt_version",
    ):
        op.drop_column("classification_rollout_events", column)
