"""Create onboarding_templates table.

Revision ID: 049
Revises: 048
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

from alembic import op

revision: str = "049"
down_revision: str | None = "048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("onboarding_templates"):
        op.create_table(
            "onboarding_templates",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("template_type", sa.String(length=20), nullable=False),
            sa.Column("key", sa.String(length=40), nullable=False),
            sa.Column("display_name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("template_body", sa.Text(), nullable=True),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_onboarding_templates_template_type",
            "onboarding_templates",
            ["template_type"],
        )
        op.create_index(
            "ix_onboarding_templates_is_archived",
            "onboarding_templates",
            ["is_archived"],
        )
        op.create_index(
            "ux_onboarding_templates_type_key",
            "onboarding_templates",
            ["template_type", "key"],
            unique=True,
        )


def downgrade() -> None:
    if _has_table("onboarding_templates"):
        op.drop_table("onboarding_templates")
