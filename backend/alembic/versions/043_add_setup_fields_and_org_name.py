"""Add setup state fields and organization_name to organization_settings.

Revision ID: 043
Revises: 042
Create Date: 2026-07-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '043'
down_revision = '042'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('organization_settings', sa.Column('organization_name', sa.String(255), nullable=True))
    op.add_column('organization_settings', sa.Column('setup_completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('organization_settings', sa.Column('setup_locked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('organization_settings', 'setup_locked_at')
    op.drop_column('organization_settings', 'setup_completed_at')
    op.drop_column('organization_settings', 'organization_name')
