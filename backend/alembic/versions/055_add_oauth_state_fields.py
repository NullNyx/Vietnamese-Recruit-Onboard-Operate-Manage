"""Add OAuth state fields to organization Google connections.

Revision ID: 055
Revises: 054
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "055"
down_revision: str | None = "054"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organization_google_connections",
        sa.Column("oauth_state_hash", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "organization_google_connections",
        sa.Column("oauth_state_nonce", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "organization_google_connections",
        sa.Column("oauth_state_session_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "organization_google_connections",
        sa.Column("oauth_state_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_organization_google_connections_oauth_state_hash",
        "organization_google_connections",
        ["oauth_state_hash"],
    )
    op.create_index(
        "ix_organization_google_connections_oauth_state_session_id",
        "organization_google_connections",
        ["oauth_state_session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_organization_google_connections_oauth_state_session_id",
        table_name="organization_google_connections",
    )
    op.drop_index(
        "ix_organization_google_connections_oauth_state_hash",
        table_name="organization_google_connections",
    )
    op.drop_column("organization_google_connections", "oauth_state_expires_at")
    op.drop_column("organization_google_connections", "oauth_state_session_id")
    op.drop_column("organization_google_connections", "oauth_state_nonce")
    op.drop_column("organization_google_connections", "oauth_state_hash")
