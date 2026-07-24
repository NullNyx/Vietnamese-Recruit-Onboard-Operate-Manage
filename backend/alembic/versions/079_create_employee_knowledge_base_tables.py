"""Create employee_knowledge_base_documents and employee_knowledge_base_chunks tables.

Revision ID: 079
Revises: 078
Create Date: 2026-07-19 01:00:00.000000+00:00

Adds the two Employee Knowledge Base tables (Issue #260, KB-04):
- employee_knowledge_base_documents: metadata for uploaded Employee documents.
- employee_knowledge_base_chunks: chunked text with pgvector embeddings.

Schema is identical to HR KB tables (078) for physical security isolation.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "079"
down_revision: str | None = "078"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "employee_knowledge_base_documents",
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
            server_default="employee",
            comment="employee — the type of knowledge base this doc belongs to",
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
        "employee_knowledge_base_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("employee_knowledge_base_documents.id", ondelete="CASCADE"),
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
    op.create_index("ix_emp_kb_documents_status", "employee_knowledge_base_documents", ["status"])
    op.create_index("ix_emp_kb_documents_kb_type", "employee_knowledge_base_documents", ["kb_type"])
    op.create_index(
        "ix_emp_kb_chunks_document_id", "employee_knowledge_base_chunks", ["document_id"]
    )


def downgrade() -> None:
    op.drop_table("employee_knowledge_base_chunks")
    op.drop_table("employee_knowledge_base_documents")
