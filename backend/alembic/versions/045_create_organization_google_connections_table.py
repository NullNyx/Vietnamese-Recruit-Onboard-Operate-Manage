"""Create organization_google_connections table.

Revision ID: 045
Revises: 044
Create Date: 2026-07-11 00:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "045"
down_revision: Union[str, None] = "044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organization_google_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_singleton_key", sa.String(length=32), nullable=False, server_default="default"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="disconnected"),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("google_sub", sa.String(length=255), nullable=True),
        sa.Column("email_domain", sa.String(length=255), nullable=True),
        sa.Column("selected_calendar_id", sa.String(length=255), nullable=True),
        sa.Column("credential_format_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("credential_key_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("access_token_enc", sa.Text(), nullable=True),
        sa.Column("refresh_token_enc", sa.Text(), nullable=True),
        sa.Column("client_secret_enc", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connected_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["connected_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("organization_singleton_key", name="uq_organization_google_connections_singleton_key"),
    )


def downgrade() -> None:
    op.drop_table("organization_google_connections")
