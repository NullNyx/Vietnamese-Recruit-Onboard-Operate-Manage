"""Add allowed_domains to organization_settings.

Adds a TEXT[] column to the single-row ``organization_settings`` table
so the Organization can store a list of email domains permitted for
employee login.  Default ``'{}'`` (empty array) means no restriction,
keeping existing deployments backwards-compatible.

Revision ID: 030
Revises: 029
Create Date: 2026-06-03
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "030"
down_revision: str | None = "029"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "organization_settings",
        sa.Column(
            "allowed_domains",
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("organization_settings", "allowed_domains")
