"""Create attendance and payroll tables.

Creates tables for the MVP: attendance_records, work_shifts,
attendance_settings, overtime_configs, salary_configs, allowances,
and payroll_records.

Revision ID: 030
Revises: 029
Create Date: 2026-06-02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "030"
down_revision: str = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Attendance Records
    op.create_table(
        "attendance_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False, index=True),
        sa.Column("checkin_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checkout_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="web"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("location_id", sa.String(100), nullable=True),
        sa.Column("work_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("late_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("early_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_late", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_early_leave", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("edited_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Work Shifts
    op.create_table(
        "work_shifts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("break_start", sa.Time, nullable=True),
        sa.Column("break_end", sa.Time, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Attendance Settings
    op.create_table(
        "attendance_settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("work_model", sa.String(20), nullable=False, server_default="fixed"),
        sa.Column("checkin_web_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("checkin_qr_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("checkin_device_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("fixed_start_time", sa.Time, nullable=False, server_default=sa.text("time '08:00'")),
        sa.Column("fixed_end_time", sa.Time, nullable=False, server_default=sa.text("time '17:00'")),
        sa.Column("fixed_break_start", sa.Time, nullable=False, server_default=sa.text("time '12:00'")),
        sa.Column("fixed_break_end", sa.Time, nullable=False, server_default=sa.text("time '13:00'")),
        sa.Column("late_tolerance_minutes", sa.Integer, nullable=False, server_default="10"),
        sa.Column("early_leave_tolerance_minutes", sa.Integer, nullable=False, server_default="10"),
        sa.Column("weekly_off_days", sa.String(50), nullable=False, server_default="saturday"),
        sa.Column("ip_whitelist_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ip_whitelist", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Overtime Configs
    op.create_table(
        "overtime_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("day_type", sa.String(20), nullable=False),
        sa.Column("rate", sa.Numeric(3, 1), nullable=False, server_default="1.5"),
        sa.Column("max_hours_per_day", sa.Numeric(3, 1), nullable=True),
        sa.Column("max_hours_per_month", sa.Numeric(5, 1), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )

    # Salary Configs
    op.create_table(
        "salary_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False, unique=True, index=True),
        sa.Column("gross_salary", sa.Numeric(15, 2), nullable=False),
        sa.Column("pay_cycle", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("work_days_per_month", sa.Integer, nullable=False, server_default="26"),
        sa.Column("work_hours_per_day", sa.Integer, nullable=False, server_default="8"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Allowances
    op.create_table(
        "allowances",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("calculation_type", sa.String(20), nullable=False, server_default="fixed"),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("include_in_tax", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("include_in_insurance", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("applies_to", sa.String(20), nullable=False, server_default="all"),
        sa.Column("applies_to_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Payroll Records
    op.create_table(
        "payroll_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False, index=True),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("gross_salary", sa.Numeric(15, 2), nullable=False),
        sa.Column("work_days_actual", sa.Numeric(5, 2), nullable=False),
        sa.Column("salary_based_on_days", sa.Numeric(15, 2), nullable=False),
        sa.Column("overtime_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("total_allowances", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("total_deductions", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("insurance_employee", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("insurance_company", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("personal_deduction", sa.Numeric(15, 2), nullable=False, server_default="11000000"),
        sa.Column("dependent_deduction", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("taxable_income", sa.Numeric(15, 2), nullable=False),
        sa.Column("personal_income_tax", sa.Numeric(15, 2), nullable=False),
        sa.Column("net_salary", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("locked_by", UUID(as_uuid=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Unique constraint for payroll_records per employee per month
    op.create_unique_constraint(
        "uq_payroll_records_employee_month_year",
        "payroll_records",
        ["employee_id", "month", "year"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_payroll_records_employee_month_year", "payroll_records")
    op.drop_table("payroll_records")
    op.drop_table("allowances")
    op.drop_table("salary_configs")
    op.drop_table("overtime_configs")
    op.drop_table("attendance_settings")
    op.drop_table("work_shifts")
    op.drop_table("attendance_records")
