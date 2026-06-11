"""API schemas for Employee Request module."""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OvertimeCreateRequest(BaseModel):
    """Request schema for creating an overtime request."""

    work_date: date = Field(description="Date overtime is worked")
    start_time: time = Field(description="Start time (HH:MM)")
    end_time: time = Field(description="End time (HH:MM, must be after start_time)")
    reason: str = Field(min_length=1, max_length=2000, description="Reason for overtime")
    project_or_task: str | None = Field(
        default=None,
        max_length=255,
        description="Optional project or task name",
    )

    @field_validator("reason")
    @classmethod
    def reject_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Reason cannot be whitespace-only")
        return v.strip()

    @field_validator("end_time")
    @classmethod
    def reject_end_before_start(cls, v: time, info) -> time:
        start = info.data.get("start_time") if info.data else None
        if start is not None and v <= start:
            raise ValueError("End time must be after start time")
        return v


class OvertimeCancelRequest(BaseModel):
    """Request schema for cancelling an overtime request."""

    cancellation_reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional reason for cancellation",
    )


class OvertimeResponse(BaseModel):
    """Response schema for an overtime request."""

    id: UUID
    employee_id: UUID
    status: str
    work_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    reason: str | None = None
    project_or_task: str | None = None
    submitted_at: datetime | None = None
    updated_at: datetime | None = None
    cancellation_reason: str | None = None

    model_config = {"from_attributes": True}


class OvertimeCreateResponse(BaseModel):
    """Response schema for successful overtime creation."""

    message: str
    request: OvertimeResponse


class OvertimeCancelResponse(BaseModel):
    """Response schema for successful overtime cancellation."""

    message: str
    request: OvertimeResponse


class OvertimeListResponse(BaseModel):
    """Response schema for listing overtime requests."""

    requests: list[OvertimeResponse]
