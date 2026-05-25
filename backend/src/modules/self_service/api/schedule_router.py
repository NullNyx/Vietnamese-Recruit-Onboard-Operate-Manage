"""ESS Schedule Router.

Provides employee self-service schedule endpoint:
- View active work schedule with upcoming holidays

All endpoints enforce ownership via the `check_ess_rate_limit` dependency,
which authenticates the employee and applies rate limiting.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.modules.attendance.domain.entities import (
    AttendanceRecord,
    Holiday,
    WorkSchedule,
)
from src.modules.attendance.infrastructure.schedule_repository import (
    ScheduleRepository,
)
from src.modules.identity.container import get_db_session
from src.modules.self_service.api.rate_limiter import check_ess_rate_limit
from src.modules.self_service.api.schemas import (
    ESSScheduleResponse,
    HolidayResponse,
)

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

EmployeeIdDep = Annotated[UUID, Depends(check_ess_rate_limit)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

schedule_router = APIRouter(prefix="/schedule", tags=["ess-schedule"])


async def _get_employee_schedule(
    employee_id: UUID, session: AsyncSession
) -> WorkSchedule | None:
    """Resolve the active work schedule for an employee.

    Strategy:
    1. Look at the employee's most recent attendance record with a schedule_id.
    2. If found, fetch that schedule.
    3. Otherwise, fall back to the default schedule.

    Args:
        employee_id: The authenticated employee's UUID.
        session: The async database session.

    Returns:
        The WorkSchedule assigned to the employee, or None if no schedule exists.
    """
    # Try to find schedule from the employee's most recent attendance record
    stmt = (
        select(AttendanceRecord.schedule_id)
        .where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.schedule_id.isnot(None),  # type: ignore[union-attr]
        )
        .order_by(col(AttendanceRecord.work_date).desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    schedule_id = result.scalar_one_or_none()

    schedule_repo = ScheduleRepository(session)

    if schedule_id:
        schedule = await schedule_repo.get_by_id(schedule_id)
        if schedule:
            return schedule

    # Fall back to default schedule
    return await schedule_repo.get_default()


async def _get_upcoming_holidays(session: AsyncSession) -> list[Holiday]:
    """Fetch upcoming holidays from today onwards for the current year.

    Args:
        session: The async database session.

    Returns:
        List of upcoming Holiday entities ordered by date.
    """
    today = date.today()
    stmt = (
        select(Holiday)
        .where(Holiday.holiday_date >= today)
        .order_by(col(Holiday.holiday_date))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


@schedule_router.get(
    "",
    summary="Get work schedule",
)
async def get_schedule(
    employee_id: EmployeeIdDep,
    session: DbSessionDep,
) -> ESSScheduleResponse | dict:
    """Get the authenticated employee's active work schedule.

    Returns the work schedule including shift times and working days,
    along with upcoming holidays. If no schedule is assigned, returns
    a message indicating no schedule is configured.

    Returns:
        ESSScheduleResponse with schedule details and holidays, or
        a dict with a message field if no schedule is assigned.
    """
    schedule = await _get_employee_schedule(employee_id, session)

    if schedule is None:
        return {"message": "No work schedule is currently assigned to your profile."}

    # Fetch upcoming holidays
    holidays = await _get_upcoming_holidays(session)
    holiday_responses = [
        HolidayResponse(
            holiday_date=h.holiday_date,
            name=h.name,
        )
        for h in holidays
    ]

    # The WorkSchedule model doesn't have a working_days column.
    # Derive a sensible default based on the schedule name.
    working_days = "Mon-Fri"

    return ESSScheduleResponse(
        schedule_name=schedule.name,
        shift_start=schedule.start_time,
        shift_end=schedule.end_time,
        working_days=working_days,
        holidays=holiday_responses,
    )
