"""Employee Self-Service Attendance Service.

Provides self-service attendance operations for employees:
- View today's attendance status
- Self check-in / check-out
- View monthly attendance history with summary

All operations are scoped to the authenticated employee_id.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from src.modules.attendance.domain.entities import AttendanceRecord, WorkSchedule
from src.modules.attendance.domain.enums import AttendanceStatus
from src.modules.attendance.infrastructure.attendance_repository import (
    AttendanceRepository,
)
from src.modules.attendance.infrastructure.schedule_repository import (
    ScheduleRepository,
)


class ESSAttendanceService:
    """Self-service attendance operations for employees.

    Wraps the attendance repository with ownership-scoped logic
    for check-in, check-out, and history retrieval.

    Args:
        attendance_repo: Repository for attendance record persistence.
        schedule_repo: Repository for work schedule lookups.
    """

    def __init__(
        self,
        attendance_repo: AttendanceRepository,
        schedule_repo: ScheduleRepository,
    ) -> None:
        self._attendance_repo = attendance_repo
        self._schedule_repo = schedule_repo

    async def get_today_status(
        self, employee_id: UUID
    ) -> AttendanceRecord | None:
        """Get today's attendance record for the employee.

        Args:
            employee_id: The authenticated employee's UUID.

        Returns:
            The attendance record for today, or None if not checked in.
        """
        today = datetime.now(UTC).date()
        return await self._attendance_repo.get_by_employee_date(employee_id, today)

    async def check_in(self, employee_id: UUID) -> AttendanceRecord:
        """Record self check-in for the employee.

        Creates a new attendance record with the current server timestamp.
        Rejects if the employee has already checked in today.

        Args:
            employee_id: The authenticated employee's UUID.

        Returns:
            The created AttendanceRecord.

        Raises:
            HTTPException: 409 if already checked in today.
        """
        now = datetime.now(UTC)
        today = now.date()

        # Check if already checked in today
        existing = await self._attendance_repo.get_by_employee_date(employee_id, today)
        if existing and existing.check_in:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ALREADY_CHECKED_IN",
                    "message": "Already checked in today",
                },
            )

        # Get schedule to determine status
        schedule = await self._schedule_repo.get_default()
        status = self._determine_checkin_status(now, schedule)

        record = AttendanceRecord(
            employee_id=employee_id,
            work_date=today,
            schedule_id=schedule.id if schedule else None,
            check_in=now,
            status=status,
        )

        return await self._attendance_repo.create(record)

    async def check_out(self, employee_id: UUID) -> AttendanceRecord:
        """Record self check-out for the employee.

        Updates the existing attendance record with check-out time and
        calculates work_hours. Rejects if not checked in or already
        checked out.

        Args:
            employee_id: The authenticated employee's UUID.

        Returns:
            The updated AttendanceRecord.

        Raises:
            HTTPException: 409 if not checked in or already checked out.
        """
        now = datetime.now(UTC)
        today = now.date()

        record = await self._attendance_repo.get_by_employee_date(employee_id, today)

        if record is None or record.check_in is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "NOT_CHECKED_IN",
                    "message": "Not checked in today",
                },
            )

        if record.check_out is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ALREADY_CHECKED_OUT",
                    "message": "Already checked out today",
                },
            )

        # Get schedule for break_minutes
        schedule = await self._schedule_repo.get_default()
        break_minutes = schedule.break_minutes if schedule else 60

        # Calculate work hours
        work_hours = self._calculate_work_hours(
            record.check_in, now, break_minutes
        )

        # Update record
        record.check_out = now
        record.work_hours = work_hours
        record.updated_at = datetime.now(UTC)

        return await self._attendance_repo.update(record)

    async def get_history(
        self, employee_id: UUID, month: int, year: int
    ) -> dict:
        """Get monthly attendance history with summary.

        Returns all attendance records for the given month/year
        along with a computed monthly summary.

        Args:
            employee_id: The authenticated employee's UUID.
            month: Month number (1-12).
            year: Year (e.g. 2024).

        Returns:
            Dictionary with 'records' list and 'summary' dict containing
            total_work_days, total_work_hours, total_overtime_hours,
            late_count, and early_departure_count.
        """
        records = await self._attendance_repo.get_monthly_report(
            employee_id, year, month
        )

        summary = self._compute_monthly_summary(records)

        return {
            "records": records,
            "summary": summary,
        }

    # ─── Private helpers ───────────────────────────────────────────────

    @staticmethod
    def _calculate_work_hours(
        check_in: datetime, check_out: datetime, break_minutes: int
    ) -> Decimal:
        """Calculate work hours from check-in/out minus break time.

        Formula: work_hours = (check_out - check_in).total_seconds() / 3600
                              - break_minutes / 60
        Result is clamped to a minimum of 0.

        Args:
            check_in: Check-in timestamp.
            check_out: Check-out timestamp.
            break_minutes: Break duration in minutes.

        Returns:
            Work hours as a Decimal, minimum 0.
        """
        diff_hours = (check_out - check_in).total_seconds() / 3600
        break_hours = break_minutes / 60
        work = max(0.0, diff_hours - break_hours)
        return Decimal(str(round(work, 2)))

    @staticmethod
    def _determine_checkin_status(
        check_in_time: datetime, schedule: WorkSchedule | None
    ) -> str:
        """Determine attendance status based on check-in time vs schedule.

        Args:
            check_in_time: The check-in datetime.
            schedule: The work schedule (may be None).

        Returns:
            Attendance status string ('present' or 'late').
        """
        if schedule is None:
            return AttendanceStatus.PRESENT

        from datetime import timedelta

        schedule_start = datetime.combine(
            check_in_time.date(), schedule.start_time, tzinfo=UTC
        )
        threshold = schedule_start + timedelta(
            minutes=schedule.late_threshold_minutes
        )

        if check_in_time > threshold:
            return AttendanceStatus.LATE
        return AttendanceStatus.PRESENT

    @staticmethod
    def _compute_monthly_summary(records: list[AttendanceRecord]) -> dict:
        """Compute monthly attendance summary from records.

        Args:
            records: List of attendance records for the month.

        Returns:
            Summary dict with total_work_days, total_work_hours,
            total_overtime_hours, late_count, early_departure_count.
        """
        counted_statuses = {
            AttendanceStatus.PRESENT,
            AttendanceStatus.LATE,
            AttendanceStatus.EARLY_LEAVE,
        }

        total_work_days = sum(
            1 for r in records if r.status in counted_statuses
        )
        total_work_hours = sum(
            float(r.work_hours or 0) for r in records
        )
        total_overtime_hours = sum(
            float(r.overtime_hours or 0) for r in records
        )
        late_count = sum(
            1 for r in records if r.status == AttendanceStatus.LATE
        )
        early_departure_count = sum(
            1 for r in records if r.status == AttendanceStatus.EARLY_LEAVE
        )

        return {
            "total_work_days": total_work_days,
            "total_work_hours": Decimal(str(round(total_work_hours, 2))),
            "total_overtime_hours": Decimal(str(round(total_overtime_hours, 2))),
            "late_count": late_count,
            "early_departure_count": early_departure_count,
        }
