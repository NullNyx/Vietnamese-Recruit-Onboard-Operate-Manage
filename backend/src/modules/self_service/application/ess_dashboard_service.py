"""Employee Self-Service Dashboard Service.

Aggregates data from multiple sources to provide a unified dashboard
overview for the authenticated employee, including:
- Today's attendance status
- Pending leave and overtime request counts
- Current month's attendance summary
- Remaining annual leave balance
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.attendance.domain.entities import (
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    OvertimeRequest,
)
from src.modules.attendance.domain.enums import AttendanceStatus, LeaveTypeCode
from src.modules.attendance.infrastructure.attendance_repository import (
    AttendanceRepository,
)
from src.modules.self_service.api.schemas import (
    AttendanceStatusEnum,
    ESSDashboardResponse,
    MonthlySummary,
)


class ESSDashboardService:
    """Aggregates dashboard data for the employee self-service portal.

    Combines attendance status, pending request counts, monthly summary,
    and annual leave balance into a single response.

    Args:
        attendance_repo: Repository for attendance record queries.
        session: Async database session for direct queries.
    """

    def __init__(
        self,
        attendance_repo: AttendanceRepository,
        session: AsyncSession,
    ) -> None:
        self._attendance_repo = attendance_repo
        self._session = session

    async def get_dashboard(self, employee_id: UUID) -> ESSDashboardResponse:
        """Aggregate all dashboard data for the given employee.

        Args:
            employee_id: The authenticated employee's UUID.

        Returns:
            ESSDashboardResponse with today's status, pending counts,
            monthly summary, and annual leave remaining.
        """
        today = datetime.now(UTC).date()

        # Gather all data concurrently-safe (sequential for simplicity
        # since we share a single session)
        today_attendance = await self._get_today_attendance_status(employee_id, today)
        pending_leave_count = await self._get_pending_leave_count(employee_id)
        pending_overtime_count = await self._get_pending_overtime_count(employee_id)
        monthly_summary = await self._get_monthly_summary(
            employee_id, today.year, today.month
        )
        annual_leave_remaining = await self._get_annual_leave_remaining(
            employee_id, today.year
        )

        return ESSDashboardResponse(
            today_attendance=today_attendance,
            pending_leave_count=pending_leave_count,
            pending_overtime_count=pending_overtime_count,
            monthly_summary=monthly_summary,
            annual_leave_remaining=annual_leave_remaining,
        )

    async def _get_today_attendance_status(
        self, employee_id: UUID, today: date
    ) -> AttendanceStatusEnum:
        """Determine today's attendance status for the employee.

        Mapping:
        - No record → not_checked_in
        - Record with check_in but no check_out → checked_in
        - Record with both check_in and check_out → checked_out

        Args:
            employee_id: The employee's UUID.
            today: Today's date.

        Returns:
            AttendanceStatusEnum value.
        """
        record = await self._attendance_repo.get_by_employee_date(employee_id, today)

        if record is None:
            return AttendanceStatusEnum.not_checked_in

        if record.check_in and not record.check_out:
            return AttendanceStatusEnum.checked_in

        if record.check_in and record.check_out:
            return AttendanceStatusEnum.checked_out

        # Edge case: record exists but no check_in (shouldn't happen normally)
        return AttendanceStatusEnum.not_checked_in

    async def _get_pending_leave_count(self, employee_id: UUID) -> int:
        """Count pending leave requests for the employee.

        Args:
            employee_id: The employee's UUID.

        Returns:
            Number of pending leave requests.
        """
        stmt = select(func.count()).select_from(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "pending",
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def _get_pending_overtime_count(self, employee_id: UUID) -> int:
        """Count pending overtime requests for the employee.

        Args:
            employee_id: The employee's UUID.

        Returns:
            Number of pending overtime requests.
        """
        stmt = select(func.count()).select_from(OvertimeRequest).where(
            OvertimeRequest.employee_id == employee_id,
            OvertimeRequest.status == "pending",
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def _get_monthly_summary(
        self, employee_id: UUID, year: int, month: int
    ) -> MonthlySummary:
        """Compute current month's attendance summary.

        Calculates days_worked (records with present/late/early_leave status),
        days_absent (records with absent status), and total_hours (sum of
        work_hours across all records).

        Args:
            employee_id: The employee's UUID.
            year: Current year.
            month: Current month.

        Returns:
            MonthlySummary with days_worked, days_absent, total_hours.
        """
        records = await self._attendance_repo.get_monthly_report(
            employee_id, year, month
        )

        worked_statuses = {
            AttendanceStatus.PRESENT,
            AttendanceStatus.LATE,
            AttendanceStatus.EARLY_LEAVE,
        }

        days_worked = sum(1 for r in records if r.status in worked_statuses)
        days_absent = sum(
            1 for r in records if r.status == AttendanceStatus.ABSENT
        )
        total_hours = sum(float(r.work_hours or 0) for r in records)

        return MonthlySummary(
            days_worked=days_worked,
            days_absent=days_absent,
            total_hours=Decimal(str(round(total_hours, 2))),
        )

    async def _get_annual_leave_remaining(
        self, employee_id: UUID, year: int
    ) -> Decimal | None:
        """Get remaining annual leave balance for the current year.

        Looks up the leave balance for the "annual" leave type.
        Returns None if no annual leave balance is configured.

        Args:
            employee_id: The employee's UUID.
            year: Current year.

        Returns:
            Remaining annual leave days, or None if not configured.
        """
        # Find the "annual" leave type
        stmt = select(LeaveType).where(LeaveType.name == LeaveTypeCode.ANNUAL)
        result = await self._session.execute(stmt)
        annual_type = result.scalars().first()

        if annual_type is None:
            return None

        # Query the balance for this employee, type, and year
        stmt = select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == annual_type.id,
            LeaveBalance.year == year,
        )
        result = await self._session.execute(stmt)
        balance = result.scalars().first()

        if balance is None:
            return None

        return balance.remaining_days
