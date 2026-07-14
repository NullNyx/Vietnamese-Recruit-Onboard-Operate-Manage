"""Store CV draft provenance, validation findings and HR confirmations.

Revision ID: 069
Revises: 068
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "069"
down_revision: str | None = "068"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cv_documents", sa.Column("field_provenance", sa.JSON(), nullable=True))
    op.add_column(
        "cv_documents",
        sa.Column("confirmed_fields", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.alter_column("cv_documents", "confirmed_fields", server_default=None)


def downgrade() -> None:
    op.drop_column("cv_documents", "confirmed_fields")
    op.drop_column("cv_documents", "field_provenance")
