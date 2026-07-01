"""Add password_hash column, widen role column.

Revision ID: 043
Revises: 042
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

revision: str = "043"
down_revision: str | None = "042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return name in columns


def upgrade() -> None:
    # Add password_hash column (nullable) for migration from OAuth-only auth
    if not _has_column("users", "password_hash"):
        op.add_column(
            "users",
            sa.Column("password_hash", sa.String(length=255), nullable=True),
        )

    # Widen role column from String(10) to String(20) for "super_admin" support
    # alembic batch context required for column type change on SQLite;
    # PostgreSQL handles ALTER COLUMN TYPE natively via op.alter_column.
    op.alter_column(
        "users",
        "role",
        type_=sa.String(length=20),
        existing_type=sa.String(length=10),
        existing_nullable=False,
        existing_server_default=sa.text("'user'"),
    )


def downgrade() -> None:
    if _has_column("users", "password_hash"):
        op.drop_column("users", "password_hash")

    op.alter_column(
        "users",
        "role",
        type_=sa.String(length=10),
        existing_type=sa.String(length=20),
        existing_nullable=False,
        existing_server_default=sa.text("'user'"),
    )
