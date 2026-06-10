"""API schemas for Attendance module."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class NetworkAllowlistResponse(BaseModel):
    """Response schema for network allowlist."""

    networks: list[str] = Field(default_factory=list, description="List of CIDR notations")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class NetworkAllowlistUpdate(BaseModel):
    """Request schema for updating network allowlist."""

    networks: list[str] = Field(
        default_factory=list, description="List of CIDR notations to replace current allowlist"
    )


class NetworkAddRequest(BaseModel):
    """Request schema for adding CIDRs to allowlist."""

    networks: list[str] = Field(min_length=1, description="List of CIDR notations to add")


class NetworkRemoveRequest(BaseModel):
    """Request schema for removing CIDR from allowlist."""

    cidr: str = Field(description="CIDR notation to remove")


class AttendanceRecordResponse(BaseModel):
    """Response schema for attendance record."""

    id: UUID
    employee_id: UUID
    work_date: date
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    check_in_ip: str | None = None
    check_out_ip: str | None = None
    source: str = "web"
    employee_name: str | None = None
    employee_code: str | None = None
    corrected_at: datetime | None = None
    correction_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CheckInResponse(BaseModel):
    """Response schema for check-in operation."""

    message: str
    record: AttendanceRecordResponse


class CheckOutResponse(BaseModel):
    """Response schema for check-out operation."""

    message: str
    record: AttendanceRecordResponse


class HistoryResponse(BaseModel):
    """Response schema for attendance history."""

    records: list[AttendanceRecordResponse] = Field(
        default_factory=list, description="List of attendance records for the month"
    )
    year: int = Field(description="Year of the requested month")
    month: int = Field(description="Month of the requested month (1-12)")


# HR Admin schemas


class AttendanceListRequest(BaseModel):
    """Request schema for listing attendance records."""

    start_date: date = Field(description="Start date for filter range")
    end_date: date = Field(description="End date for filter range")
    employee_id: UUID | None = Field(default=None, description="Filter by employee ID")
    status: Literal["checked_in", "completed"] | None = Field(
        default=None,
        description="Filter by status: checked_in or completed",
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Records per page")


class AttendanceListResponse(BaseModel):
    """Response schema for attendance record list."""

    records: list[AttendanceRecordResponse] = Field(default_factory=list)
    total: int = Field(description="Total number of records matching filters")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Records per page")


class CorrectionRequest(BaseModel):
    """Request schema for correcting an attendance record."""

    check_in_at: datetime | None = Field(
        default=None,
        description="New check-in time (null to clear)",
    )
    check_out_at: datetime | None = Field(
        default=None,
        description="New check-out time (null to clear)",
    )
    correction_reason: str = Field(
        min_length=1,
        description="Required reason for the correction",
    )

    @field_validator("correction_reason")
    @classmethod
    def reject_whitespace_only(cls, v: str) -> str:
        """Reject whitespace-only values."""
        if not v.strip():
            raise ValueError("Correction reason cannot be whitespace-only")
        return v.strip()

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> "CorrectionRequest":
        """Ensure at least one of check_in_at or check_out_at is provided."""
        if self.check_in_at is None and self.check_out_at is None:
            raise ValueError("At least one of check_in_at or check_out_at must be provided")
        return self


class CorrectionResponse(BaseModel):
    """Response schema for attendance record correction."""

    message: str
    record: AttendanceRecordResponse
