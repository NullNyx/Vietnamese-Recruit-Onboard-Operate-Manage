"""Add employee record contract entities and status fields.

Revision ID: 045
Revises: 044
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector

revision: str = "045"
down_revision: str | None = "044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return name in inspector.get_table_names()


def _has_column(table: str, name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return name in {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    if _has_table("employees"):
        if _has_column("employees", "tax_code") and not _has_column("employees", "personal_tax_code"):
            op.alter_column("employees", "tax_code", new_column_name="personal_tax_code")
        if not _has_column("employees", "employment_status"):
            op.add_column(
                "employees",
                sa.Column(
                    "employment_status",
                    sa.String(length=20),
                    nullable=False,
                    server_default=sa.text("'active'"),
                ),
            )
        if not _has_column("employees", "termination_date"):
            op.add_column(
                "employees",
                sa.Column("termination_date", sa.Date(), nullable=True),
            )
        op.alter_column(
            "employees",
            "email",
            existing_type=sa.String(length=255),
            nullable=True,
            existing_nullable=False,
        )

    if _has_table("employee_documents"):
        if not _has_column("employee_documents", "status"):
            op.add_column(
                "employee_documents",
                sa.Column(
                    "status",
                    sa.String(length=20),
                    nullable=False,
                    server_default=sa.text("'uploaded'"),
                ),
            )
        if not _has_column("employee_documents", "uploaded_by_hr_id"):
            op.add_column(
                "employee_documents",
                sa.Column("uploaded_by_hr_id", sa.Uuid(), nullable=False),
            )
        if not _has_column("employee_documents", "verified_by_hr_id"):
            op.add_column(
                "employee_documents",
                sa.Column("verified_by_hr_id", sa.Uuid(), nullable=True),
            )
        if not _has_column("employee_documents", "verified_at"):
            op.add_column(
                "employee_documents",
                sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            )
        if not _has_column("employee_documents", "expired_at"):
            op.add_column(
                "employee_documents",
                sa.Column("expired_at", sa.Date(), nullable=True),
            )

    if not _has_table("employment_events"):
        op.create_table(
            "employment_events",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("employee_id", sa.Uuid(), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("before_json", sa.JSON(), nullable=True),
            sa.Column("after_json", sa.JSON(), nullable=True),
            sa.Column("actor_hr_id", sa.Uuid(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
            sa.ForeignKeyConstraint(["actor_hr_id"], ["users.id"]),
        )
        op.create_index(
            "ix_employment_events_employee_id",
            "employment_events",
            ["employee_id"],
        )

    if not _has_table("contract_templates"):
        op.create_table(
            "contract_templates",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("file_path", sa.Text(), nullable=True),
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default=sa.text("'active'"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("created_by", sa.Uuid(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        )

    if not _has_table("contracts"):
        op.create_table(
            "contracts",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("employee_id", sa.Uuid(), nullable=False),
            sa.Column("contract_number", sa.String(length=50), nullable=True),
            sa.Column("template_id", sa.Uuid(), nullable=True),
            sa.Column("contract_type", sa.String(length=30), nullable=False),
            sa.Column(
                "status",
                sa.String(length=30),
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column("signed_on", sa.Date(), nullable=True),
            sa.Column("started_on", sa.Date(), nullable=True),
            sa.Column("ended_on", sa.Date(), nullable=True),
            sa.Column("file_path", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("signed_document_path", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("created_by", sa.Uuid(), nullable=False),
            sa.Column("updated_by", sa.Uuid(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
            sa.ForeignKeyConstraint(["template_id"], ["contract_templates.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        )
        op.create_index("ix_contracts_employee_id", "contracts", ["employee_id"])
        op.create_index("ix_contracts_contract_number", "contracts", ["contract_number"], unique=True)

    if not _has_table("contract_amendments"):
        op.create_table(
            "contract_amendments",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("contract_id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("file_path", sa.Text(), nullable=True),
            sa.Column("signed_document_path", sa.Text(), nullable=True),
            sa.Column(
                "status",
                sa.String(length=30),
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column("signed_on", sa.Date(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("created_by", sa.Uuid(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        )
        op.create_index(
            "ix_contract_amendments_contract_id",
            "contract_amendments",
            ["contract_id"],
        )


def downgrade() -> None:
    if _has_table("contract_amendments"):
        op.drop_index("ix_contract_amendments_contract_id", table_name="contract_amendments")
        op.drop_table("contract_amendments")

    if _has_table("contracts"):
        op.drop_index("ix_contracts_contract_number", table_name="contracts")
        op.drop_index("ix_contracts_employee_id", table_name="contracts")
        op.drop_table("contracts")

    if _has_table("contract_templates"):
        op.drop_table("contract_templates")

    if _has_table("employment_events"):
        op.drop_index("ix_employment_events_employee_id", table_name="employment_events")
        op.drop_table("employment_events")

    if _has_table("employee_documents"):
        for column_name in [
            "expired_at",
            "verified_at",
            "verified_by_hr_id",
            "uploaded_by_hr_id",
            "status",
        ]:
            if _has_column("employee_documents", column_name):
                op.drop_column("employee_documents", column_name)

    if _has_table("employees"):
        if _has_column("employees", "termination_date"):
            op.drop_column("employees", "termination_date")
        if _has_column("employees", "employment_status"):
            op.drop_column("employees", "employment_status")
        if _has_column("employees", "personal_tax_code") and not _has_column("employees", "tax_code"):
            op.alter_column("employees", "personal_tax_code", new_column_name="tax_code")
        op.alter_column(
            "employees",
            "email",
            existing_type=sa.String(length=255),
            nullable=False,
            existing_nullable=True,
        )
