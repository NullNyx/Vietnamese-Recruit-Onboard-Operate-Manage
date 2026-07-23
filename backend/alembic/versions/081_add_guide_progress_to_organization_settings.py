"""Add guide_progress JSONB column to organization_settings.

Revision ID: 081
Revises: 080
Create Date: 2026-07-23 00:00:00.000000+00:00

Adds a JSONB column to track Quick-Start Guide progress
(completed_tasks, dismissed) per ADR-0008.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "081"
down_revision: Union[str, None] = "080"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organization_settings",
        sa.Column("guide_progress", JSONB, nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("organization_settings", "guide_progress")
