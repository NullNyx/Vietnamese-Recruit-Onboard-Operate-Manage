"""Domain entities for the Attendance & Payroll module.

Defines SQLModel table classes for attendance records, work shifts,
attendance settings, payroll salary configs, allowances, and payroll records.
"""

from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Numeric, Time
from sqlmodel import Field, SQLModel


class AttendanceRecord(SQLModel, table=True):
    """A single attendance check-in/check-out record for an employee."""

    __tablename__ = "attendance_records"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(foreign_key="employees.id", nullable=False, index=True)
    checkin_time: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    checkout_time: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    source: str = Field(
        default="web",
        max_length=20,
        nullable=False,
    )  # web, qr, device
    ip_address: str | None = Field(default=None, max_length=45)
    location_id: str | None = Field(default=None, max_length=100)
    work_hours: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 2), nullable=True),
    )
    late_minutes: int = Field(default=0, nullable=False)
    early_minutes: int = Field(default=0, nullable=False)
    is_late: bool = Field(default=False, nullable=False)
    is_early_leave: bool = Field(default=False, nullable=False)
    notes: str | None = Field(default=None)
    edited_by: UUID | None = Field(default=None)  # HR who edited
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class WorkShift(SQLModel, table=True):
    """A defined work shift (e.g., Morning 06:00-14:00)."""

    __tablename__ = "work_shifts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, nullable=False)
    start_time: time = Field(
        sa_column=Column(Time, nullable=False),
    )
    end_time: time = Field(
        sa_column=Column(Time, nullable=False),
    )
    break_start: time | None = Field(
        default=None,
        sa_column=Column(Time, nullable=True),
    )
    break_end: time | None = Field(
        default=None,
        sa_column=Column(Time, nullable=True),
    )
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AttendanceSettings(SQLModel, table=True):
    """Company-wide attendance configuration."""

    __tablename__ = "attendance_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    work_model: str = Field(
        default="fixed",
        max_length=20,
        nullable=False,
    )  # fixed, shift, flexible, hybrid
    checkin_web_enabled: bool = Field(default=True, nullable=False)
    checkin_qr_enabled: bool = Field(default=True, nullable=False)
    checkin_device_enabled: bool = Field(default=False, nullable=False)
    fixed_start_time: time = Field(
        default=time(8, 0),
        sa_column=Column(Time, nullable=False),
    )
    fixed_end_time: time = Field(
        default=time(17, 0),
        sa_column=Column(Time, nullable=False),
    )
    fixed_break_start: time = Field(
        default=time(12, 0),
        sa_column=Column(Time, nullable=False),
    )
    fixed_break_end: time = Field(
        default=time(13, 0),
        sa_column=Column(Time, nullable=False),
    )
    late_tolerance_minutes: int = Field(default=10, nullable=False)
    early_leave_tolerance_minutes: int = Field(default=10, nullable=False)
    weekly_off_days: str = Field(
        default="saturday",
        max_length=50,
        nullable=False,
    )  # saturday, sunday, custom
    ip_whitelist_enabled: bool = Field(default=False, nullable=False)
    ip_whitelist: str | None = Field(default=None)  # comma-separated IPs
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class OvertimeConfig(SQLModel, table=True):
    """Overtime rate configuration."""

    __tablename__ = "overtime_configs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    day_type: str = Field(
        max_length=20,
        nullable=False,
    )  # weekday, saturday, sunday, holiday
    rate: Decimal = Field(
        default=Decimal("1.5"),
        sa_column=Column(Numeric(3, 1), nullable=False),
    )
    max_hours_per_day: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(3, 1), nullable=True),
    )
    max_hours_per_month: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 1), nullable=True),
    )
    is_active: bool = Field(default=True, nullable=False)


class SalaryConfig(SQLModel, table=True):
    """Employee salary configuration."""

    __tablename__ = "salary_configs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(
        foreign_key="employees.id",
        unique=True,
        nullable=False,
        index=True,
    )
    gross_salary: Decimal = Field(
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    pay_cycle: str = Field(
        default="monthly",
        max_length=20,
        nullable=False,
    )  # monthly, bimonthly
    work_days_per_month: int = Field(default=26, nullable=False)
    work_hours_per_day: int = Field(default=8, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Allowance(SQLModel, table=True):
    """Employee allowance (dynamic per company)."""

    __tablename__ = "allowances"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, nullable=False)
    calculation_type: str = Field(
        default="fixed",
        max_length=20,
        nullable=False,
    )  # fixed, per_day, percent_gross
    amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    include_in_tax: bool = Field(default=True, nullable=False)
    include_in_insurance: bool = Field(default=False, nullable=False)
    applies_to: str = Field(
        default="all",
        max_length=20,
        nullable=False,
    )  # all, department, employee
    applies_to_id: UUID | None = Field(default=None)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class PayrollRecord(SQLModel, table=True):
    """Monthly payroll record for an employee."""

    __tablename__ = "payroll_records"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(
        foreign_key="employees.id",
        nullable=False,
        index=True,
    )
    month: int = Field(nullable=False)
    year: int = Field(nullable=False)
    gross_salary: Decimal = Field(
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    work_days_actual: Decimal = Field(
        sa_column=Column(Numeric(5, 2), nullable=False),
    )
    salary_based_on_days: Decimal = Field(
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    overtime_amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    total_allowances: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    total_deductions: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    insurance_employee: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    insurance_company: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    personal_deduction: Decimal = Field(
        default=Decimal("11000000"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    dependent_deduction: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    taxable_income: Decimal = Field(
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    personal_income_tax: Decimal = Field(
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    net_salary: Decimal = Field(
        sa_column=Column(Numeric(15, 2), nullable=False),
    )
    status: str = Field(
        default="draft",
        max_length=20,
        nullable=False,
    )  # draft, locked, paid
    locked_by: UUID | None = Field(default=None)
    locked_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
