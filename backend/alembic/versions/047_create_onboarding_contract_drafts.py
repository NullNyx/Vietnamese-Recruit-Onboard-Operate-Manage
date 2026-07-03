"""Create onboarding_contract_drafts table.

Revision ID: 047
Revises: 046
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

from alembic import op

revision: str = "047"
down_revision: str | None = "046"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("onboarding_contract_drafts"):
        op.create_table(
            "onboarding_contract_drafts",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("process_id", sa.Uuid(), nullable=False, unique=True),
            sa.Column("contract_type", sa.String(length=30), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column(
                "status", sa.String(length=20), nullable=False, server_default=sa.text("'draft'")
            ),
            sa.Column("revision", sa.Integer(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_by", sa.Uuid(), nullable=True),
            sa.Column("updated_by", sa.Uuid(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["process_id"],
                ["onboarding_processes.id"],
            ),
            sa.ForeignKeyConstraint(
                ["created_by"],
                ["users.id"],
            ),
            sa.ForeignKeyConstraint(
                ["updated_by"],
                ["users.id"],
            ),
        )
        op.create_index(
            "ix_onboarding_contract_drafts_process_id",
            "onboarding_contract_drafts",
            ["process_id"],
            unique=True,
        )


def downgrade() -> None:
    if _has_table("onboarding_contract_drafts"):
        op.drop_table("onboarding_contract_drafts")
