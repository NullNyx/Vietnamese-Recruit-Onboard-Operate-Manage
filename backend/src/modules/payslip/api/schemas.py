"""API schemas for Payslip module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.modules.payslip.domain.entities import PayslipStatus


class PayslipResponse(BaseModel):
    """Response schema for a single payslip."""

    id: UUID
    employee_id: UUID
    period_month: date
    gross_salary: Decimal
    deductions: Decimal
    insurance_employee: Decimal
    taxable_income: Decimal
    pit_amount: Decimal
    net_salary: Decimal
    currency: str = "VND"
    status: PayslipStatus
    published_at: datetime | None = None
    pdf_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PayslipListResponse(BaseModel):
    """Response schema for payslip list."""

    payslips: list[PayslipResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Admin schemas
# ---------------------------------------------------------------------------


class CreatePayslipRequest(BaseModel):
    """Request schema for creating a draft Payslip."""

    employee_id: UUID
    period_month: date
    gross_salary: Decimal = Field(gt=0, decimal_places=2, max_digits=12)
    deductions: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2, max_digits=12)
    insurance_employee: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2, max_digits=12)
    taxable_income: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2, max_digits=12)
    pit_amount: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2, max_digits=12)
    net_salary: Decimal = Field(gt=0, decimal_places=2, max_digits=12)
    pdf_url: str | None = None
    currency: str = Field(default="VND", pattern=r"^VND$")

    @field_validator("period_month")
    @classmethod
    def normalize_period_month(cls, v: date) -> date:
        """Normalize period_month to first day of month."""
        if v.day != 1:
            return v.replace(day=1)
        return v


class UpdatePayslipRequest(BaseModel):
    """Request schema for updating a draft Payslip.

    All fields are optional; only provided fields will be updated.
    Use a sentinel value (empty string) to clear pdf_url.
    """

    gross_salary: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=12)
    deductions: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    insurance_employee: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    taxable_income: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    pit_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    net_salary: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=12)
    pdf_url: str | None = Field(default=None, max_length=500)

    @field_validator("pdf_url", mode="before")
    @classmethod
    def normalize_pdf_url(cls, v: str | None) -> str | None:
        """Convert empty string to None to allow clearing pdf_url."""
        if v == "":
            return None
        return v


class AdminPayslipListResponse(BaseModel):
    """Response schema for admin payslip list with filters."""

    payslips: list[PayslipResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
