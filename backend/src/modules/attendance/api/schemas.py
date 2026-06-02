"""Pydantic schemas for Attendance & Payroll API."""

from datetime import datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ===================== Check-in/Check-out Schemas =====================


class CheckinRequest(BaseModel):
    """Request body for check-in."""

    employee_id: UUID
    timestamp: datetime | None = None  # Optional, defaults to server time
    source: str = "web"  # web, qr, device
    ip_address: str | None = None
    location_id: str | None = None


class CheckinResponse(BaseModel):
    """Response after successful check-in."""

    id: UUID
    employee_id: UUID
    checkin_time: datetime
    source: str
    is_late: bool
    late_minutes: int


class CheckoutRequest(BaseModel):
    """Request body for check-out."""

    employee_id: UUID
    timestamp: datetime | None = None  # Optional, defaults to server time


class CheckoutResponse(BaseModel):
    """Response after successful check-out."""

    id: UUID
    employee_id: UUID
    checkin_time: datetime
    checkout_time: datetime
    work_hours: Decimal
    is_early_leave: bool
    early_minutes: int


# ===================== Attendance Record Schemas =====================


class AttendanceRecordResponse(BaseModel):
    """Attendance record response."""

    id: UUID
    employee_id: UUID
    checkin_time: datetime
    checkout_time: datetime | None
    source: str
    work_hours: Decimal | None
    late_minutes: int
    early_minutes: int
    is_late: bool
    is_early_leave: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceHistoryResponse(BaseModel):
    """Paginated attendance history."""

    items: list[AttendanceRecordResponse]
    total: int
    page: int
    page_size: int


class HREditRecordRequest(BaseModel):
    """HR edit attendance record request."""

    checkin_time: datetime | None = None
    checkout_time: datetime | None = None
    notes: str | None = None


# ===================== Settings Schemas =====================


class AttendanceSettingsResponse(BaseModel):
    """Attendance settings response."""

    id: UUID
    work_model: str
    checkin_web_enabled: bool
    checkin_qr_enabled: bool
    checkin_device_enabled: bool
    fixed_start_time: time
    fixed_end_time: time
    fixed_break_start: time
    fixed_break_end: time
    late_tolerance_minutes: int
    early_leave_tolerance_minutes: int
    weekly_off_days: str
    ip_whitelist_enabled: bool
    ip_whitelist: str | None

    model_config = {"from_attributes": True}


class AttendanceSettingsUpdate(BaseModel):
    """Attendance settings update request."""

    work_model: str | None = None
    checkin_web_enabled: bool | None = None
    checkin_qr_enabled: bool | None = None
    checkin_device_enabled: bool | None = None
    fixed_start_time: time | None = None
    fixed_end_time: time | None = None
    fixed_break_start: time | None = None
    fixed_break_end: time | None = None
    late_tolerance_minutes: int | None = None
    early_leave_tolerance_minutes: int | None = None
    weekly_off_days: str | None = None
    ip_whitelist_enabled: bool | None = None
    ip_whitelist: str | None = None


# ===================== Salary Config Schemas =====================


class SalaryConfigRequest(BaseModel):
    """Request to set employee salary config."""

    employee_id: UUID
    gross_salary: Decimal = Field(gt=0)
    pay_cycle: str = "monthly"
    work_days_per_month: int = Field(default=26, ge=20, le=31)
    work_hours_per_day: int = Field(default=8, ge=6, le=12)


class SalaryConfigResponse(BaseModel):
    """Salary config response."""

    id: UUID
    employee_id: UUID
    gross_salary: Decimal
    pay_cycle: str
    work_days_per_month: int
    work_hours_per_day: int
    is_active: bool

    model_config = {"from_attributes": True}


# ===================== Payroll Schemas =====================


class PayrollCalculateRequest(BaseModel):
    """Request to calculate payroll for a month."""

    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020)


class PayrollRecordResponse(BaseModel):
    """Payroll record response."""

    id: UUID
    employee_id: UUID
    month: int
    year: int
    gross_salary: Decimal
    work_days_actual: Decimal
    salary_based_on_days: Decimal
    overtime_amount: Decimal
    total_allowances: Decimal
    insurance_employee: Decimal
    insurance_company: Decimal
    personal_deduction: Decimal
    dependent_deduction: Decimal
    taxable_income: Decimal
    personal_income_tax: Decimal
    net_salary: Decimal
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PayslipResponse(BaseModel):
    """Simplified payslip for employee view."""

    month: int
    year: int
    gross_salary: Decimal
    work_days_actual: Decimal
    overtime_amount: Decimal
    total_allowances: Decimal
    insurance_employee: Decimal
    personal_income_tax: Decimal
    net_salary: Decimal
    status: str

    model_config = {"from_attributes": True}


# ===================== Error Schemas =====================


class AttendanceErrorResponse(BaseModel):
    """Error response."""

    detail: str


# ===================== QR Check-in Schemas =====================


class QRCheckinRequest(BaseModel):
    """QR check-in request."""

    qr_code: str
    employee_id: UUID
    ip_address: str | None = None


class QRGenerateResponse(BaseModel):
    """QR code generation response."""

    qr_code: str
    location_id: str
    expires_at: datetime
