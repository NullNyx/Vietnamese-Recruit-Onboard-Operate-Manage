"""Enable pgvector extension for Knowledge Base RAG vector storage.

Revision ID: 077
Revises: 076
Create Date: 2026-07-18 00:00:00.000000+00:00

Adds the ``vector`` extension to PostgreSQL so that tables can define
``vector(768)`` columns for embedding storage. This is the infrastructure
foundation for the Knowledge Base RAG feature (Issue #256, #257).
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "077"
down_revision: Union[str, None] = "076"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
