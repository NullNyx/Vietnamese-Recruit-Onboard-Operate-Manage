"""Add data policy consent and independent AI capability toggles.

Revision ID: 058
Revises: 057
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "058"
down_revision: str | None = "057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "data_policy_accepted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "data_policy_accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "data_policy_accepted_by_user_id",
            sa.Uuid(),
            nullable=True,
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "data_policy_version",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "ai_automation_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "ai_assistant_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_foreign_key(
        "fk_ai_config_data_policy_user",
        "organization_ai_configurations",
        "users",
        ["data_policy_accepted_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ai_config_data_policy_user",
        "organization_ai_configurations",
        type_="foreignkey",
    )
    op.drop_column("organization_ai_configurations", "ai_assistant_enabled")
    op.drop_column("organization_ai_configurations", "ai_automation_enabled")
    op.drop_column("organization_ai_configurations", "data_policy_version")
    op.drop_column("organization_ai_configurations", "data_policy_accepted_by_user_id")
    op.drop_column("organization_ai_configurations", "data_policy_accepted_at")
    op.drop_column("organization_ai_configurations", "data_policy_accepted")
