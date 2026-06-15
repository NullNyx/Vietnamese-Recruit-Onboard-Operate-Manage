"""Domain entities for the Payslip module.

Defines the Payslip SQLModel table for read-only payslip access.
HR manually creates and publishes Payslips; Employees view only
their own published Payslips (ADR-0012).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Payslip(SQLModel, table=True):
    """Payroll statement for one Employee and one pay period.

    Stores explicit payroll amounts set by HR. No automatic calculation
    from attendance or overtime (see ADR-0012). Employees can view only
    their own published Payslips.
    """

    __tablename__ = "payslips"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(
        nullable=False,
        foreign_key="employees.id",
        index=True,
    )
    pay_period_start: date = Field(nullable=False)
    pay_period_end: date = Field(nullable=False)

    # Payroll amounts — explicit values set by HR
    gross_amount: Decimal = Field(
        nullable=False,
        max_digits=12,
        decimal_places=2,
    )
    total_deductions: Decimal = Field(
        default=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    net_amount: Decimal = Field(
        nullable=False,
        max_digits=12,
        decimal_places=2,
    )

    currency: str = Field(default="VND", max_length=3)

    # Flexible breakdown for allowances, OT, tax, insurance, etc.
    details: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Publication state
    published: bool = Field(default=False, nullable=False)
    published_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Optional PDF reference
    pdf_url: str | None = Field(default=None, max_length=500)

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "pay_period_start",
            "pay_period_end",
            name="uq_payslips_employee_pay_period",
        ),
        CheckConstraint(
            "(published = false AND published_at IS NULL)"
            " OR (published = true AND published_at IS NOT NULL)",
            name="ck_payslips_published_at_consistent",
        ),
    )
