"""Create setup_state table.

Revision ID: 044
Revises: 043
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

revision: str = "044"
down_revision: str | None = "043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("setup_state"):
        op.create_table(
            "setup_state",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_by_user_id", sa.String(length=36), nullable=True),
            sa.Column("org_name", sa.String(length=255), nullable=True),
            sa.Column("org_tax_code", sa.String(length=20), nullable=True),
            sa.Column("org_timezone", sa.String(length=64), nullable=True),
            sa.Column("ai_provider", sa.String(length=50), nullable=True),
            sa.Column("ai_api_key_enc", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    if _has_table("setup_state"):
        op.drop_table("setup_state")
