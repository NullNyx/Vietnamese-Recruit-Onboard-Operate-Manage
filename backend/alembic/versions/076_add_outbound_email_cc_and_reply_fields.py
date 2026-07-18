"""Add cc_recipients and reply_to_message_id columns to outbound_emails.

Revision ID: 076
Revises: 075
Create Date: 2026-07-17 00:00:00.000000+00:00

Supports the frontend ComposeDialog which sends CC recipients and
reply-to message IDs for Gmail threading.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "076"
down_revision: Union[str, None] = "075"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "outbound_emails",
        sa.Column("cc_recipients", sa.Text(), nullable=True),
    )
    op.add_column(
        "outbound_emails",
        sa.Column("reply_to_message_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("outbound_emails", "reply_to_message_id")
    op.drop_column("outbound_emails", "cc_recipients")
