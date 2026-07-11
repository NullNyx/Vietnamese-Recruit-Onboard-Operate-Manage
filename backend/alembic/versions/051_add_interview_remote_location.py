"""Add remote_location column to interviews for calendar sync.

Adds a nullable ``remote_location`` column to the ``interviews`` table
so the CalendarSyncService can persist the physical/remote meeting
location from a Google Calendar event during sync (GH #156).

Revision ID: 051
Revises: 050
Create Date: 2026-07-11 18:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "051"
down_revision: Union[str, None] = "050"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interviews",
        sa.Column("remote_location", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interviews", "remote_location")
