"""Pydantic request/response schemas for the Employee Self-Service API.

Defines data transfer objects used by the ESS router endpoints
for structured data validation and serialization.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AttendanceStatusEnum(str, Enum):
    """Today's attendance status for the dashboard."""

    checked_in = "checked_in"
    not_checked_in = "not_checked_in"
    checked_out = "checked_out"


# ---------------------------------------------------------------------------
# Profile schemas
# ---------------------------------------------------------------------------


class ESSProfileResponse(BaseModel):
    """Response schema for an employee viewing their own profile.

    Sensitive fields (id_number, tax_code) are masked to show only
    the last 4 characters.

    Attributes:
        full_name: Employee's full name.
        email: Employee's email address.
        phone: Phone number, if provided.
        date_of_birth: Date of birth, if provided.
        gender: Gender, if provided.
        address: Home address, if provided.
        department_name: Name of assigned department, if any.
        position_name: Name of assigned position, if any.
        start_date: Employment start date, if provided.
        contract_type: Type of employment contract, if provided.
        id_number_masked: Masked national ID (e.g., "****1234").
        tax_code_masked: Masked tax code (e.g., "****5678").
    """

    model_config = ConfigDict(from_attributes=True)

    full_name: str
    email: str
    phone: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    address: str | None = None
    department_name: str | None = None
    position_name: str | None = None
    start_date: date | None = None
    contract_type: str | None = None
    id_number_masked: str | None = None
    tax_code_masked: str | None = None


class ESSProfileUpdateRequest(BaseModel):
    """Request schema for updating allowed profile fields.

    Only phone, address, and emergency_contact may be modified by
    the employee. All other fields are restricted.

    Attributes:
        phone: Vietnamese phone number (10 digits starting with 0).
        address: Home address (max 500 characters).
        emergency_contact: Emergency contact info (max 255 characters).
    """

    phone: str | None = Field(None, pattern=r"^0\d{9}$")
    address: str | None = Field(None, max_length=500)
    emergency_contact: str | None = Field(None, max_length=255)


# ---------------------------------------------------------------------------
# Attendance schemas
# ---------------------------------------------------------------------------


class ESSAttendanceRecordResponse(BaseModel):
    """Response schema for a single attendance record.

    Attributes:
        id: Unique attendance record identifier.
        work_date: The date of this attendance record.
        check_in: Check-in timestamp, if recorded.
        check_out: Check-out timestamp, if recorded.
        work_hours: Calculated work hours for the day.
        overtime_hours: Overtime hours for the day.
        status: Attendance status (present, late, early_leave, etc.).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    work_hours: Decimal | None = None
    overtime_hours: Decimal = Decimal("0")
    status: str


class ESSAttendanceSummaryResponse(BaseModel):
    """Response schema for monthly attendance summary.

    Attributes:
        total_work_days: Number of days with present/late/early_leave status.
        total_work_hours: Sum of work_hours across all records in the month.
        total_overtime_hours: Sum of overtime_hours across all records.
        late_count: Number of days marked as late.
        early_departure_count: Number of days with early departure.
    """

    total_work_days: int
    total_work_hours: Decimal
    total_overtime_hours: Decimal
    late_count: int
    early_departure_count: int


# ---------------------------------------------------------------------------
# Leave schemas
# ---------------------------------------------------------------------------


class ESSLeaveRequestCreate(BaseModel):
    """Request schema for submitting a new leave request.

    Attributes:
        leave_type_id: UUID of the leave type being requested.
        start_date: First day of leave (must not be in the past).
        end_date: Last day of leave (must be >= start_date).
        reason: Optional reason for the leave request.
    """

    leave_type_id: UUID
    start_date: date
    end_date: date
    reason: str | None = Field(None, max_length=500)


class ESSLeaveRequestResponse(BaseModel):
    """Response schema for a leave request.

    Attributes:
        id: Unique leave request identifier.
        leave_type_name: Display name of the leave type.
        start_date: First day of leave.
        end_date: Last day of leave.
        total_days: Total number of leave days requested.
        status: Current status (pending, approved, rejected, cancelled).
        reason: Reason provided by the employee, if any.
        created_at: When the request was submitted.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    leave_type_name: str
    start_date: date
    end_date: date
    total_days: Decimal
    status: str
    reason: str | None = None
    created_at: datetime


class ESSLeaveBalanceResponse(BaseModel):
    """Response schema for a leave balance entry.

    Attributes:
        leave_type_id: UUID of the leave type.
        leave_type_name: Display name of the leave type.
        total_days: Total allocated days for the year.
        used_days: Days already used.
        remaining_days: Days still available.
    """

    model_config = ConfigDict(from_attributes=True)

    leave_type_id: UUID
    leave_type_name: str
    total_days: Decimal
    used_days: Decimal
    remaining_days: Decimal


# ---------------------------------------------------------------------------
# Overtime schemas
# ---------------------------------------------------------------------------


class ESSOvertimeRequestCreate(BaseModel):
    """Request schema for submitting a new overtime request.

    Attributes:
        work_date: Date of planned overtime (must not be in the past).
        planned_hours: Planned overtime hours (0.5 to 4.0).
        reason: Reason for the overtime request (required, max 500 chars).
    """

    work_date: date
    planned_hours: Decimal = Field(ge=Decimal("0.5"), le=Decimal("4.0"))
    reason: str = Field(max_length=500)


class ESSOvertimeRequestResponse(BaseModel):
    """Response schema for an overtime request.

    Attributes:
        id: Unique overtime request identifier.
        work_date: Date of the overtime.
        planned_hours: Planned overtime hours.
        actual_hours: Actual overtime hours recorded, if any.
        status: Current status (pending, approved, rejected).
        reason: Reason provided by the employee.
        created_at: When the request was submitted.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_date: date
    planned_hours: Decimal
    actual_hours: Decimal | None = None
    status: str
    reason: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------


class ESSDocumentResponse(BaseModel):
    """Response schema for an employee document.

    Attributes:
        id: Unique document identifier.
        file_name: Original file name.
        document_type: Category of document (e.g., cccd, degree, contract).
        file_size: File size in bytes.
        uploaded_at: When the document was uploaded.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    document_type: str
    file_size: int
    uploaded_at: datetime


# ---------------------------------------------------------------------------
# Schedule schemas
# ---------------------------------------------------------------------------


class HolidayResponse(BaseModel):
    """Response schema for a holiday entry.

    Attributes:
        holiday_date: Date of the holiday.
        name: Name of the holiday.
    """

    model_config = ConfigDict(from_attributes=True)

    holiday_date: date
    name: str


class ESSScheduleResponse(BaseModel):
    """Response schema for an employee's work schedule.

    Attributes:
        schedule_name: Name of the work schedule.
        shift_start: Shift start time.
        shift_end: Shift end time.
        working_days: Description of working days (e.g., "Mon-Fri").
        holidays: List of upcoming holidays.
    """

    schedule_name: str
    shift_start: time
    shift_end: time
    working_days: str
    holidays: list[HolidayResponse] = []


# ---------------------------------------------------------------------------
# Dashboard schemas
# ---------------------------------------------------------------------------


class MonthlySummary(BaseModel):
    """Monthly attendance summary for the dashboard.

    Attributes:
        days_worked: Number of days worked in the current month.
        days_absent: Number of days absent in the current month.
        total_hours: Total work hours in the current month.
    """

    days_worked: int
    days_absent: int
    total_hours: Decimal


class ESSDashboardResponse(BaseModel):
    """Response schema for the employee dashboard overview.

    Aggregates today's attendance status, pending request counts,
    monthly summary, and annual leave balance.

    Attributes:
        today_attendance: Current attendance status for today.
        pending_leave_count: Number of pending leave requests.
        pending_overtime_count: Number of pending overtime requests.
        monthly_summary: Current month's attendance summary.
        annual_leave_remaining: Remaining annual leave days, if available.
    """

    today_attendance: AttendanceStatusEnum
    pending_leave_count: int
    pending_overtime_count: int
    monthly_summary: MonthlySummary
    annual_leave_remaining: Decimal | None = None
