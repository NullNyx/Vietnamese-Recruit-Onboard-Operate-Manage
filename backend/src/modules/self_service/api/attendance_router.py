"""ESS Attendance Router.

Provides employee self-service attendance endpoints:
- View today's attendance status
- Self check-in
- Self check-out
- View monthly attendance history with summary

All endpoints enforce ownership via the `check_ess_rate_limit` dependency,
which authenticates the employee and applies rate limiting.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.modules.self_service.api.rate_limiter import check_ess_rate_limit
from src.modules.self_service.api.schemas import (
    ESSAttendanceRecordResponse,
    ESSAttendanceSummaryResponse,
)
from src.modules.self_service.application.ess_attendance_service import (
    ESSAttendanceService,
)
from src.modules.self_service.container import get_ess_attendance_service

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

EmployeeIdDep = Annotated[UUID, Depends(check_ess_rate_limit)]


ESSAttendanceServiceDep = Annotated[
    ESSAttendanceService, Depends(get_ess_attendance_service)
]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

attendance_router = APIRouter(prefix="/attendance", tags=["ess-attendance"])


@attendance_router.get(
    "/today",
    response_model=ESSAttendanceRecordResponse | None,
    summary="Get today's attendance status",
)
async def get_today_status(
    employee_id: EmployeeIdDep,
    service: ESSAttendanceServiceDep,
) -> ESSAttendanceRecordResponse | None:
    """Get the authenticated employee's attendance record for today.

    Returns the attendance record if the employee has checked in today,
    or None if no record exists yet.
    """
    record = await service.get_today_status(employee_id)
    if record is None:
        return None
    return ESSAttendanceRecordResponse.model_validate(record)


@attendance_router.post(
    "/check-in",
    response_model=ESSAttendanceRecordResponse,
    status_code=201,
    summary="Self check-in",
)
async def check_in(
    employee_id: EmployeeIdDep,
    service: ESSAttendanceServiceDep,
) -> ESSAttendanceRecordResponse:
    """Record self check-in for the authenticated employee.

    Creates a new attendance record with the current server timestamp.
    Returns 409 if the employee has already checked in today.
    """
    record = await service.check_in(employee_id)
    return ESSAttendanceRecordResponse.model_validate(record)


@attendance_router.post(
    "/check-out",
    response_model=ESSAttendanceRecordResponse,
    summary="Self check-out",
)
async def check_out(
    employee_id: EmployeeIdDep,
    service: ESSAttendanceServiceDep,
) -> ESSAttendanceRecordResponse:
    """Record self check-out for the authenticated employee.

    Updates the existing attendance record with the check-out timestamp
    and calculates work hours. Returns 409 if not checked in or already
    checked out today.
    """
    record = await service.check_out(employee_id)
    return ESSAttendanceRecordResponse.model_validate(record)


@attendance_router.get(
    "/history",
    summary="Get monthly attendance history",
)
async def get_history(
    employee_id: EmployeeIdDep,
    service: ESSAttendanceServiceDep,
    month: int = Query(ge=1, le=12, description="Month number (1-12)"),
    year: int = Query(ge=2020, le=2100, description="Year (e.g. 2024)"),
) -> dict:
    """Get the authenticated employee's monthly attendance history.

    Returns all attendance records for the specified month/year along
    with a computed monthly summary including total work days, hours,
    overtime, late arrivals, and early departures.

    Query Parameters:
        month: Month number (1-12), required.
        year: Year (e.g. 2024), required.
    """
    result = await service.get_history(employee_id, month, year)

    records = [
        ESSAttendanceRecordResponse.model_validate(r) for r in result["records"]
    ]
    summary = ESSAttendanceSummaryResponse(**result["summary"])

    return {
        "records": records,
        "summary": summary,
    }
