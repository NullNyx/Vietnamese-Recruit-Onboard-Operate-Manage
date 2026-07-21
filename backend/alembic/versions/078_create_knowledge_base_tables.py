"""Create hr_knowledge_base_documents and hr_knowledge_base_chunks tables.

Revision ID: 078
Revises: 077
Create Date: 2026-07-19 00:00:00.000000+00:00

Adds the two core tables for the Knowledge Base RAG feature (Issue #256, #258):
- hr_knowledge_base_documents: metadata for uploaded HR documents.
- hr_knowledge_base_chunks: chunked text with pgvector embeddings.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "078"
down_revision: Union[str, None] = "077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hr_knowledge_base_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("display_name", sa.String(500), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="general"),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(200), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="pending | processing | ready | error",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "kb_type",
            sa.String(20),
            nullable=False,
            server_default="hr",
            comment="hr (default) — the type of knowledge base this doc belongs to",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "hr_knowledge_base_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("hr_knowledge_base_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Index for fast document lookups and status-based queries
    op.create_index("ix_kb_documents_status", "hr_knowledge_base_documents", ["status"])
    op.create_index("ix_kb_documents_kb_type", "hr_knowledge_base_documents", ["kb_type"])
    op.create_index("ix_kb_chunks_document_id", "hr_knowledge_base_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_table("hr_knowledge_base_chunks")
    op.drop_table("hr_knowledge_base_documents")
