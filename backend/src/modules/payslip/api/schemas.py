"""API schemas for Payslip module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PayslipResponse(BaseModel):
    """Response schema for a single payslip."""

    id: UUID
    employee_id: UUID
    pay_period_start: date
    pay_period_end: date
    gross_amount: Decimal
    total_deductions: Decimal
    net_amount: Decimal
    currency: str = "VND"
    details: dict | None = None
    pdf_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class PayslipListResponse(BaseModel):
    """Response schema for payslip list."""

    payslips: list[PayslipResponse] = Field(default_factory=list)
