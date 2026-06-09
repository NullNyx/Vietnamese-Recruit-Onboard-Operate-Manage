"""API schemas for Attendance module."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
