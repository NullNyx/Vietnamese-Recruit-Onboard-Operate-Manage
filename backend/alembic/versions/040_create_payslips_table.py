"""Create payslips table.

Read-only payslip surface per ADR-0012. Stores explicit payroll amounts
set by HR. No payroll engine, no automatic calculation from attendance or
overtime. Employees view only their own published Payslips.

Revision ID: 040
Revises: 039
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "040"
down_revision: str | None = "039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payslips",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.Column("pay_period_start", sa.Date(), nullable=False),
        sa.Column("pay_period_end", sa.Date(), nullable=False),
        sa.Column(
            "gross_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "total_deductions",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "net_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column("currency", sa.String(length=3), server_default="VND", nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("published", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pdf_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id",
            "pay_period_start",
            "pay_period_end",
            name="uq_payslips_employee_pay_period",
        ),
        sa.CheckConstraint(
            "(published = false AND published_at IS NULL)"
            " OR (published = true AND published_at IS NOT NULL)",
            name="ck_payslips_published_at_consistent",
        ),
    )
    op.create_index("ix_payslips_employee_id", "payslips", ["employee_id"])
    op.create_index(
        "ix_payslips_employee_published",
        "payslips",
        ["employee_id", "published"],
    )
    op.create_foreign_key(
        "fk_payslips_employee_id",
        "payslips",
        "employees",
        ["employee_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_payslips_employee_id", "payslips", type_="foreignkey")
    op.drop_index("ix_payslips_employee_published", table_name="payslips")
    op.drop_index("ix_payslips_employee_id", table_name="payslips")
    op.drop_table("payslips")
