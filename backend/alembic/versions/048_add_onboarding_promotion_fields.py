"""Add promotion fields to onboarding_documents and onboarding_contract_drafts.

Adds `promoted_employee_document_id`, `promoted_at` to onboarding_documents and
`promoted_contract_id`, `promoted_at` to onboarding_contract_drafts so the
onboarding promotion flow can track which artifacts have been promoted to the
Employee Record and what employee-module entity they became.

Revision ID: 048
Revises: 047
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

revision: str = "048"
down_revision: str | None = "047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def _has_index(table: str, name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return any(ix["name"] == name for ix in inspector.get_indexes(table))


def upgrade() -> None:
    # onboarding_documents
    if not _has_column("onboarding_documents", "promoted_employee_document_id"):
        op.add_column(
            "onboarding_documents",
            sa.Column("promoted_employee_document_id", sa.Uuid(), nullable=True),
        )
    if not _has_index("onboarding_documents", "ix_onboarding_documents_promoted_employee_document_id"):
        op.create_index(
            "ix_onboarding_documents_promoted_employee_document_id",
            "onboarding_documents",
            ["promoted_employee_document_id"],
        )
    if not _has_column("onboarding_documents", "promoted_at"):
        op.add_column(
            "onboarding_documents",
            sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # onboarding_contract_drafts
    if not _has_column("onboarding_contract_drafts", "promoted_contract_id"):
        op.add_column(
            "onboarding_contract_drafts",
            sa.Column("promoted_contract_id", sa.Uuid(), nullable=True),
        )
    if not _has_index("onboarding_contract_drafts", "ix_onboarding_contract_drafts_promoted_contract_id"):
        op.create_index(
            "ix_onboarding_contract_drafts_promoted_contract_id",
            "onboarding_contract_drafts",
            ["promoted_contract_id"],
        )
    if not _has_column("onboarding_contract_drafts", "promoted_at"):
        op.add_column(
            "onboarding_contract_drafts",
            sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    # onboarding_documents
    if _has_column("onboarding_documents", "promoted_employee_document_id"):
        if _has_index("onboarding_documents", "ix_onboarding_documents_promoted_employee_document_id"):
            op.drop_index(
                "ix_onboarding_documents_promoted_employee_document_id",
                table_name="onboarding_documents",
            )
        op.drop_column("onboarding_documents", "promoted_employee_document_id")
    if _has_column("onboarding_documents", "promoted_at"):
        op.drop_column("onboarding_documents", "promoted_at")

    # onboarding_contract_drafts
    if _has_column("onboarding_contract_drafts", "promoted_contract_id"):
        if _has_index("onboarding_contract_drafts", "ix_onboarding_contract_drafts_promoted_contract_id"):
            op.drop_index(
                "ix_onboarding_contract_drafts_promoted_contract_id",
                table_name="onboarding_contract_drafts",
            )
        op.drop_column("onboarding_contract_drafts", "promoted_contract_id")
    if _has_column("onboarding_contract_drafts", "promoted_at"):
        op.drop_column("onboarding_contract_drafts", "promoted_at")
