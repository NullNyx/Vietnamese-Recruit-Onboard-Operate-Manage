"""Add description column to HR and Employee KB document tables.

Revision ID: 080
Revises: 079
Create Date: 2026-07-20 00:00:00.000000+00:00

Adds an optional description field to both hr_knowledge_base_documents
and employee_knowledge_base_documents for richer metadata (Issue #261, KB-05).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "080"
down_revision: str | None = "079"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "hr_knowledge_base_documents",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "employee_knowledge_base_documents",
        sa.Column("description", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employee_knowledge_base_documents", "description")
    op.drop_column("hr_knowledge_base_documents", "description")
