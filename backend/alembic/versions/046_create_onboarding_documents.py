"""Create onboarding_documents table.

Revision ID: 046
Revises: 045
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine.reflection import Inspector

from alembic import op

revision: str = "046"
down_revision: str | None = "045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("onboarding_documents"):
        op.create_table(
            "onboarding_documents",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("process_id", sa.Uuid(), nullable=False),
            sa.Column("document_type", sa.String(length=40), nullable=False),
            sa.Column("display_name", sa.String(length=100), nullable=False),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column(
                "status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")
            ),
            sa.Column("file_name", sa.String(length=255), nullable=True),
            sa.Column("file_size", sa.Integer(), nullable=True),
            sa.Column("mime_type", sa.String(length=100), nullable=True),
            sa.Column("storage_path", sa.String(length=500), nullable=True),
            sa.Column("reject_reason", sa.String(length=500), nullable=True),
            sa.Column("uploaded_by_hr_id", sa.Uuid(), nullable=True),
            sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_by_hr_id", sa.Uuid(), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ai_extraction", JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["process_id"], ["onboarding_processes.id"]),
            sa.ForeignKeyConstraint(["uploaded_by_hr_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["verified_by_hr_id"], ["users.id"]),
        )
        op.create_index(
            "ix_onboarding_documents_process_id",
            "onboarding_documents",
            ["process_id"],
        )


def downgrade() -> None:
    if _has_table("onboarding_documents"):
        op.drop_table("onboarding_documents")
