"""Alter payslips table for HR manual publish flow.

Adds new fields (gross_salary, deductions, insurance_employee, taxable_income,
pit_amount, net_salary, period_month, status) and removes old fields
(pay_period_start, pay_period_end, gross_amount, total_deductions, net_amount,
published, details). Idempotent for fresh install vs upgrade from 040.

Revision ID: 041
Revises: 040
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

revision: str = "041"
down_revision: str | None = "040"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(name: str) -> bool:
    """Check if a column exists in the payslips table."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [c["name"] for c in inspector.get_columns("payslips")]
    return name in columns


def _has_constraint(name: str) -> bool:
    """Check if a constraint exists on the payslips table."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    constraints = [c["name"] for c in inspector.get_unique_constraints("payslips")]
    constraints += [c["name"] for c in inspector.get_check_constraints("payslips")]
    return name in constraints


def _has_index(name: str) -> bool:
    """Check if an index exists."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    indexes = [i["name"] for i in inspector.get_indexes("payslips")]
    return name in indexes


def upgrade() -> None:
    # --- Add new columns if they don't exist ---
    if not _has_column("period_month"):
        op.add_column(
            "payslips",
            sa.Column("period_month", sa.Date(), nullable=True),
        )
    if not _has_column("gross_salary"):
        op.add_column(
            "payslips",
            sa.Column("gross_salary", sa.Numeric(precision=12, scale=2), nullable=True),
        )
    if not _has_column("deductions"):
        op.add_column(
            "payslips",
            sa.Column("deductions", sa.Numeric(precision=12, scale=2), nullable=True),
        )
    if not _has_column("insurance_employee"):
        op.add_column(
            "payslips",
            sa.Column("insurance_employee", sa.Numeric(precision=12, scale=2), nullable=True),
        )
    if not _has_column("taxable_income"):
        op.add_column(
            "payslips",
            sa.Column("taxable_income", sa.Numeric(precision=12, scale=2), nullable=True),
        )
    if not _has_column("pit_amount"):
        op.add_column(
            "payslips",
            sa.Column("pit_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        )
    if not _has_column("net_salary"):
        op.add_column(
            "payslips",
            sa.Column("net_salary", sa.Numeric(precision=12, scale=2), nullable=True),
        )
    if not _has_column("status"):
        op.add_column(
            "payslips",
            sa.Column("status", sa.String(length=10), nullable=True),
        )

    # --- Migrate data from old columns if they exist ---
    if _has_column("pay_period_start") and _has_column("period_month"):
        op.execute("""
            UPDATE payslips
            SET period_month = pay_period_start,
                gross_salary = gross_amount,
                net_salary = net_amount,
                deductions = COALESCE(total_deductions, 0),
                status = CASE WHEN published = true THEN 'published' ELSE 'draft' END
            WHERE period_month IS NULL
        """)

    # --- Set NOT NULL and defaults on new columns ---
    op.alter_column("payslips", "period_month", nullable=False,
                    server_default=sa.text("'2026-01-01'::date"))
    op.alter_column("payslips", "gross_salary", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "deductions", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "insurance_employee", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "taxable_income", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "pit_amount", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "net_salary", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "status", nullable=False, server_default="draft")

    # --- Drop old columns if they exist ---
    for col in ["pay_period_start", "pay_period_end", "gross_amount",
                "total_deductions", "net_amount", "details", "published"]:
        if _has_column(col):
            op.drop_column("payslips", col)

    # --- Drop old constraints ---
    if _has_constraint("uq_payslips_employee_pay_period"):
        op.drop_constraint("uq_payslips_employee_pay_period", "payslips", type_="unique")
    if _has_constraint("ck_payslips_published_at_consistent"):
        op.drop_constraint(
            "ck_payslips_published_at_consistent", "payslips", type_="check"
        )

    # --- Create new constraints (if not exist) ---
    if not _has_constraint("uq_payslips_employee_period_month"):
        op.create_unique_constraint(
            "uq_payslips_employee_period_month",
            "payslips",
            ["employee_id", "period_month"],
        )
    if not _has_constraint("ck_payslips_status_published_at_consistent"):
        op.create_check_constraint(
            "ck_payslips_status_published_at_consistent",
            "payslips",
            "(status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL)",
        )

    # --- Drop old index and create new ---
    if _has_index("ix_payslips_employee_published"):
        op.drop_index("ix_payslips_employee_published", table_name="payslips")
    if not _has_index("ix_payslips_employee_status"):
        op.create_index(
            "ix_payslips_employee_status",
            "payslips",
            ["employee_id", "status"],
        )


def downgrade() -> None:
    """Reverse - restore old columns. Idempotent."""
    if not _has_column("pay_period_start"):
        op.add_column("payslips", sa.Column("pay_period_start", sa.Date(), nullable=True))
    if not _has_column("pay_period_end"):
        op.add_column("payslips", sa.Column("pay_period_end", sa.Date(), nullable=True))
    if not _has_column("gross_amount"):
        op.add_column("payslips", sa.Column("gross_amount", sa.Numeric(precision=12, scale=2), nullable=True))
    if not _has_column("total_deductions"):
        op.add_column("payslips", sa.Column("total_deductions", sa.Numeric(precision=12, scale=2), nullable=True))
    if not _has_column("net_amount"):
        op.add_column("payslips", sa.Column("net_amount", sa.Numeric(precision=12, scale=2), nullable=True))
    if not _has_column("details"):
        op.add_column("payslips", sa.Column("details", postgresql.JSONB(), nullable=True))
    if not _has_column("published"):
        op.add_column("payslips", sa.Column("published", sa.Boolean(), nullable=True))

    if _has_column("pay_period_start") and _has_column("period_month"):
        op.execute("""
            UPDATE payslips
            SET pay_period_start = period_month,
                pay_period_end = period_month + interval '1 month - 1 day',
                gross_amount = gross_salary,
                net_amount = net_salary,
                total_deductions = deductions,
                published = (status = 'published')
            WHERE pay_period_start IS NULL
        """)

    # Drop new columns
    for col in ["period_month", "gross_salary", "deductions", "insurance_employee",
                "taxable_income", "pit_amount", "net_salary", "status"]:
        if _has_column(col):
            op.drop_column("payslips", col)

    # Restore old constraints
    if _has_constraint("uq_payslips_employee_period_month"):
        op.drop_constraint("uq_payslips_employee_period_month", "payslips", type_="unique")
    if _has_constraint("ck_payslips_status_published_at_consistent"):
        op.drop_constraint(
            "ck_payslips_status_published_at_consistent", "payslips", type_="check"
        )
    if not _has_constraint("uq_payslips_employee_pay_period"):
        op.create_unique_constraint(
            "uq_payslips_employee_pay_period",
            "payslips",
            ["employee_id", "pay_period_start", "pay_period_end"],
        )
    if not _has_constraint("ck_payslips_published_at_consistent"):
        op.create_check_constraint(
            "ck_payslips_published_at_consistent",
            "payslips",
            "(published = false AND published_at IS NULL) OR (published = true AND published_at IS NOT NULL)",
        )

    if _has_index("ix_payslips_employee_status"):
        op.drop_index("ix_payslips_employee_status", table_name="payslips")
    if not _has_index("ix_payslips_employee_published"):
        op.create_index(
            "ix_payslips_employee_published",
            "payslips",
            ["employee_id", "published"],
        )
