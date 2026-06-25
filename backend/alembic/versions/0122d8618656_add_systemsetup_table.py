"""add systemsetup table

Revision ID: 0122d8618656
Revises: 041
Create Date: 2026-06-23 12:11:19.216576+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0122d8618656'
down_revision: Union[str, None] = '041'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create system_setup table
    op.create_table(
        'system_setup',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('is_setup_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('setup_token', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Backward compatibility: auto-complete setup if system has existing data
    connection = op.get_bind()
    
    # Check if users table exists and has rows
    from sqlalchemy import inspect
    inspector = inspect(connection)
    
    has_data = False
    if 'users' in inspector.get_table_names():
        users_exist = connection.execute(sa.text("SELECT 1 FROM users LIMIT 1")).scalar() is not None
        if users_exist:
            has_data = True
            
    if not has_data and 'oauth_configs' in inspector.get_table_names():
        oauth_exists = connection.execute(sa.text("SELECT 1 FROM oauth_configs LIMIT 1")).scalar() is not None
        if oauth_exists:
            has_data = True
            
    if has_data:
        import uuid
        from datetime import datetime, UTC
        connection.execute(
            sa.text(
                "INSERT INTO system_setup (id, is_setup_completed, setup_token, created_at, updated_at) "
                "VALUES (:id, :is_setup_completed, :setup_token, :created_at, :updated_at)"
            ),
            {
                "id": uuid.uuid4(),
                "is_setup_completed": True,
                "setup_token": None,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )


def downgrade() -> None:
    op.drop_table('system_setup')
