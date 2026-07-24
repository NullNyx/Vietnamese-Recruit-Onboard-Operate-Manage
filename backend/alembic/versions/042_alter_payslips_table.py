"""Alter payslips table for HR manual publish flow.

Adds new fields (gross_salary, deductions, insurance_employee, taxable_income,
pit_amount, net_salary, period_month, status) and removes old fields
(pay_period_start, pay_period_end, gross_amount, total_deductions, net_amount,
published, details). Idempotent for fresh install vs upgrade from 040.

Revision ID: 042
Revises: 041
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

from alembic import op

revision: str = "042"
down_revision: str | None = "041"
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
    # --- Drop old constraints FIRST (before dropping columns) ---
    if _has_constraint("uq_payslips_employee_pay_period"):
        op.drop_constraint("uq_payslips_employee_pay_period", "payslips", type_="unique")
    if _has_constraint("ck_payslips_published_at_consistent"):
        op.drop_constraint("ck_payslips_published_at_consistent", "payslips", type_="check")

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
                gross_salary = COALESCE(gross_amount, 0),
                net_salary = COALESCE(net_amount, 0),
                deductions = COALESCE(total_deductions, 0),
                status = CASE WHEN published = true THEN 'published' ELSE 'draft' END,
                published_at = CASE WHEN published = true THEN NOW() ELSE published_at END
            WHERE period_month IS NULL OR status IS NULL
        """)

    # --- Backfill fields without a direct legacy equivalent before enforcing NOT NULL ---
    # Server defaults only apply to future inserts; existing payslips need explicit values.
    op.execute(
        """
        UPDATE payslips
        SET insurance_employee = COALESCE(insurance_employee, 0),
            taxable_income = COALESCE(taxable_income, 0),
            pit_amount = COALESCE(pit_amount, 0)
        WHERE insurance_employee IS NULL
           OR taxable_income IS NULL
           OR pit_amount IS NULL
        """
    )

    # --- Set NOT NULL and defaults on new columns (temporary defaults for backfill) ---
    op.alter_column(
        "payslips", "period_month", nullable=False, server_default=sa.text("'2026-01-01'::date")
    )
    op.alter_column("payslips", "gross_salary", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "deductions", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "insurance_employee", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "taxable_income", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "pit_amount", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "net_salary", nullable=False, server_default=sa.text("0"))
    op.alter_column("payslips", "status", nullable=False, server_default="draft")

    # --- Drop old columns (now safe since constraints are dropped) ---
    for col in [
        "pay_period_start",
        "pay_period_end",
        "gross_amount",
        "total_deductions",
        "net_amount",
        "details",
        "published",
    ]:
        if _has_column(col):
            op.drop_column("payslips", col)

    # --- Drop old index and create new ---
    if _has_index("ix_payslips_employee_published"):
        op.drop_index("ix_payslips_employee_published", table_name="payslips")
    if not _has_index("ix_payslips_employee_status"):
        op.create_index(
            "ix_payslips_employee_status",
            "payslips",
            ["employee_id", "status"],
        )

    # --- Drop temporary defaults (after backfill is complete) ---
    op.alter_column("payslips", "period_month", server_default=None)
    op.alter_column("payslips", "gross_salary", server_default=None)
    op.alter_column("payslips", "deductions", server_default=None)
    op.alter_column("payslips", "insurance_employee", server_default=None)
    op.alter_column("payslips", "taxable_income", server_default=None)
    op.alter_column("payslips", "pit_amount", server_default=None)
    op.alter_column("payslips", "net_salary", server_default=None)

    # --- Deduplicate before creating unique constraint ---
    bind = op.get_bind()
    duplicates = bind.execute(
        sa.text("""
            SELECT employee_id, period_month, COUNT(*)
            FROM payslips
            GROUP BY employee_id, period_month
            HAVING COUNT(*) > 1
        """)
    ).fetchall()
    for row in duplicates:
        # Keep the first (oldest) record and remove duplicates
        bind.execute(
            sa.text("""
                DELETE FROM payslips
                WHERE (employee_id, period_month, id) IN (
                    SELECT employee_id, period_month, id
                    FROM (
                        SELECT id, employee_id, period_month,
                               ROW_NUMBER() OVER (
                                   PARTITION BY employee_id, period_month
                                   ORDER BY created_at ASC, id ASC
                               ) AS rn
                        FROM payslips
                        WHERE employee_id = :emp_id
                          AND period_month = :per_month
                    ) ranked
                    WHERE rn > 1
                )
            """),
            {"emp_id": row[0], "per_month": row[1]},
        )

    # --- Create new constraints ---
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

    # --- Add currency check constraint ---
    if not _has_constraint("ck_payslips_currency_vnd"):
        op.create_check_constraint(
            "ck_payslips_currency_vnd",
            "payslips",
            "currency = 'VND'",
        )


def downgrade() -> None:
    """Reverse - restore old columns. Idempotent."""
    # --- Drop new constraints first ---
    if _has_constraint("uq_payslips_employee_period_month"):
        op.drop_constraint("uq_payslips_employee_period_month", "payslips", type_="unique")
    if _has_constraint("ck_payslips_status_published_at_consistent"):
        op.drop_constraint("ck_payslips_status_published_at_consistent", "payslips", type_="check")
    if _has_constraint("ck_payslips_currency_vnd"):
        op.drop_constraint("ck_payslips_currency_vnd", "payslips", type_="check")

    # --- Drop new indexes ---
    if _has_index("ix_payslips_employee_status"):
        op.drop_index("ix_payslips_employee_status", table_name="payslips")

    # --- Add old columns back ---
    if not _has_column("pay_period_start"):
        op.add_column("payslips", sa.Column("pay_period_start", sa.Date(), nullable=True))
    if not _has_column("pay_period_end"):
        op.add_column("payslips", sa.Column("pay_period_end", sa.Date(), nullable=True))
    if not _has_column("gross_amount"):
        op.add_column(
            "payslips", sa.Column("gross_amount", sa.Numeric(precision=12, scale=2), nullable=True)
        )
    if not _has_column("total_deductions"):
        op.add_column(
            "payslips",
            sa.Column("total_deductions", sa.Numeric(precision=12, scale=2), nullable=True),
        )
    if not _has_column("net_amount"):
        op.add_column(
            "payslips", sa.Column("net_amount", sa.Numeric(precision=12, scale=2), nullable=True)
        )
    if not _has_column("details"):
        op.add_column("payslips", sa.Column("details", postgresql.JSONB(), nullable=True))
    if not _has_column("published"):
        op.add_column("payslips", sa.Column("published", sa.Boolean(), nullable=True))

    # --- Migrate data back ---
    if _has_column("pay_period_start") and _has_column("period_month"):
        op.execute("""
            UPDATE payslips
            SET pay_period_start = COALESCE(period_month, CURRENT_DATE),
                pay_period_end = COALESCE(period_month, CURRENT_DATE) + interval '1 month - 1 day',
                gross_amount = gross_salary,
                net_amount = net_salary,
                total_deductions = deductions,
                published = (status = 'published')
            WHERE pay_period_start IS NULL
        """)

    # --- Drop new columns ---
    for col in [
        "period_month",
        "gross_salary",
        "deductions",
        "insurance_employee",
        "taxable_income",
        "pit_amount",
        "net_salary",
        "status",
    ]:
        if _has_column(col):
            op.drop_column("payslips", col)

    # --- Restore old constraints ---
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

    if not _has_index("ix_payslips_employee_published"):
        op.create_index(
            "ix_payslips_employee_published",
            "payslips",
            ["employee_id", "published"],
        )
