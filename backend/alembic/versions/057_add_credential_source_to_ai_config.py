"""Add credential_source and make api_key_enc default empty for Organization AI config.

Revision ID: 057
Revises: 056
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "057"
down_revision: str | None = "056"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organization_ai_configurations",
        sa.Column(
            "credential_source",
            sa.String(length=32),
            nullable=False,
            server_default="org_api_key",
        ),
    )
    op.alter_column(
        "organization_ai_configurations",
        "api_key_enc",
        existing_type=sa.Text(),
        nullable=True,
        server_default="",
    )
    op.alter_column(
        "organization_ai_configurations",
        "updated_by_user_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )


def downgrade() -> None:
    op.drop_column("organization_ai_configurations", "credential_source")
    op.alter_column(
        "organization_ai_configurations",
        "api_key_enc",
        existing_type=sa.Text(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "organization_ai_configurations",
        "updated_by_user_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
