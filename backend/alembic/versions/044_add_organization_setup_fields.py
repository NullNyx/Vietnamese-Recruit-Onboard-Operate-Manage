"""Add Organization identity and singleton guard for First-Run Setup.

Revision ID: 044
Revises: 043
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "044"
down_revision: Union[str, None] = "043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organization_settings",
        sa.Column("singleton_key", sa.String(length=20), nullable=False, server_default="default"),
    )
    op.add_column(
        "organization_settings",
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
    )
    op.create_unique_constraint(
        "uq_organization_settings_singleton_key",
        "organization_settings",
        ["singleton_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_organization_settings_singleton_key",
        "organization_settings",
        type_="unique",
    )
    op.drop_column("organization_settings", "name")
    op.drop_column("organization_settings", "singleton_key")
