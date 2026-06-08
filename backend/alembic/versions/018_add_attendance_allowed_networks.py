"""Add attendance_allowed_networks to organization_settings.

Revision ID: 018
Revises: 017
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add attendance_allowed_networks column to organization_settings table."""
    op.add_column(
        "organization_settings",
        sa.Column(
            "attendance_allowed_networks",
            sa.ARRAY(sa.String(length=255)),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    """Remove attendance_allowed_networks column."""
    op.drop_column("organization_settings", "attendance_allowed_networks")
