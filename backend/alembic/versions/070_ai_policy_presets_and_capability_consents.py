"""Add independent AI capability consents and versioned policy preset.

Revision ID: 070
Revises: 069
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "070"
down_revision: str | None = "069"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organization_ai_configurations",
        sa.Column("ai_automation_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column("ai_assistant_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column("ai_policy_preset", sa.String(length=32), nullable=False, server_default="balanced"),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "ai_policy_preset_version",
            sa.String(length=64),
            nullable=False,
            server_default="balanced-v1",
        ),
    )
    for column in (
        "ai_automation_consent",
        "ai_assistant_consent",
        "ai_policy_preset",
        "ai_policy_preset_version",
    ):
        op.alter_column("organization_ai_configurations", column, server_default=None)


def downgrade() -> None:
    op.drop_column("organization_ai_configurations", "ai_policy_preset_version")
    op.drop_column("organization_ai_configurations", "ai_policy_preset")
    op.drop_column("organization_ai_configurations", "ai_assistant_consent")
    op.drop_column("organization_ai_configurations", "ai_automation_consent")
