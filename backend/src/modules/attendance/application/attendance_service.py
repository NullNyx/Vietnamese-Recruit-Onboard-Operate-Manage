"""Attendance business logic service.

Handles check-in, check-out, and attendance record management.
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

import logging
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from src.modules.attendance.domain.entities import (
    AttendanceRecord,
    AttendanceSettings,
)
from src.modules.attendance.infrastructure.attendance_repository import (
    AttendanceRepository,
)
from src.modules.attendance.infrastructure.settings_repository import (
    SettingsRepository,
)

logger = logging.getLogger(__name__)


class AttendanceError(Exception):
    """Base exception for attendance operations."""

    pass


class CheckinError(AttendanceError):
    """Exception for check-in failures."""

    pass


class CheckoutError(AttendanceError):
    """Exception for check-out failures."""

    pass


class AttendanceService:
    """Service for attendance business logic."""

    def __init__(
        self,
        attendance_repository: AttendanceRepository,
        settings_repository: SettingsRepository,
    ) -> None:
        self.attendance_repo = attendance_repository
        self.settings_repo = settings_repository

    async def checkin(
        self,
        employee_id: UUID,
        timestamp: datetime,
        ip_address: str | None = None,
        source: str = "web",
        location_id: str | None = None,
    ) -> AttendanceRecord:
        """Perform a check-in for an employee.

        Args:
            employee_id: UUID of the employee.
            timestamp: The check-in timestamp.
            ip_address: Optional IP address.
            source: Check-in method (web, qr, device).
            location_id: Optional location identifier.

        Returns:
            The created AttendanceRecord.

        Raises:
            CheckinError: If validation fails.
        """
        settings = await self.settings_repo.get_attendance_settings()
        if settings is None:
            raise CheckinError("Attendance settings not configured")

        # Check if already checked in today
        today = timestamp.date()
        existing = await self.attendance_repo.get_by_employee_and_date(employee_id, today)
        if existing and existing.checkout_time is None:
            raise CheckinError("Already checked in today. Check out first.")

        # Validate source is enabled
        if source == "web" and not settings.checkin_web_enabled:
            raise CheckinError("Web check-in is disabled")
        if source == "qr" and not settings.checkin_qr_enabled:
            raise CheckinError("QR check-in is disabled")
        if source == "device" and not settings.checkin_device_enabled:
            raise CheckinError("Device check-in is disabled")

        # Validate IP whitelist if enabled
        if settings.ip_whitelist_enabled and ip_address:
            whitelist = settings.ip_whitelist or ""
            allowed_ips = [ip.strip() for ip in whitelist.split(",") if ip.strip()]
            if ip_address not in allowed_ips:
                raise CheckinError(f"IP {ip_address} not in whitelist")

        # Calculate late minutes
        is_late, late_minutes = self._calculate_late(
            timestamp.time(), settings.fixed_start_time, settings.late_tolerance_minutes
        )

        # Create record
        record = AttendanceRecord(
            employee_id=employee_id,
            checkin_time=timestamp,
            source=source,
            ip_address=ip_address,
            location_id=location_id,
            late_minutes=late_minutes,
            is_late=is_late,
        )

        return await self.attendance_repo.create(record)

    async def checkout(
        self,
        employee_id: UUID,
        timestamp: datetime,
    ) -> AttendanceRecord:
        """Perform a check-out for an employee.

        Args:
            employee_id: UUID of the employee.
            timestamp: The check-out timestamp.

        Returns:
            The updated AttendanceRecord.

        Raises:
            CheckoutError: If validation fails.
        """
        settings = await self.settings_repo.get_attendance_settings()
        if settings is None:
            raise CheckoutError("Attendance settings not configured")

        # Find today's open record
        today = timestamp.date()
        record = await self.attendance_repo.get_by_employee_and_date(employee_id, today)
        if record is None:
            raise CheckoutError("No check-in record found for today")
        if record.checkout_time is not None:
            raise CheckoutError("Already checked out today")

        # Calculate work hours
        work_hours = self._calculate_work_hours(
            record.checkin_time,
            timestamp,
            settings.fixed_break_start,
            settings.fixed_break_end,
        )

        # Calculate early minutes
        is_early, early_minutes = self._calculate_early_leave(
            timestamp.time(), settings.fixed_end_time, settings.early_leave_tolerance_minutes
        )

        # Update record
        record.checkout_time = timestamp
        record.work_hours = Decimal(str(round(work_hours, 2)))
        record.early_minutes = early_minutes
        record.is_early_leave = is_early

        return await self.attendance_repo.update(record)

    async def get_attendance_history(
        self,
        employee_id: UUID,
        month: int | None = None,
        year: int | None = None,
        page: int = 1,
        page_size: int = 31,
    ) -> tuple[list[AttendanceRecord], int]:
        """Get attendance history for an employee."""
        return await self.attendance_repo.list_by_employee(
            employee_id, month, year, page, page_size
        )

    async def hr_edit_record(
        self,
        record_id: UUID,
        checkin_time: datetime | None = None,
        checkout_time: datetime | None = None,
        edited_by: UUID | None = None,
        notes: str | None = None,
    ) -> AttendanceRecord:
        """HR manually edit an attendance record.

        Args:
            record_id: UUID of the record to edit.
            checkin_time: New check-in time (optional).
            checkout_time: New check-out time (optional).
            edited_by: UUID of the HR admin.
            notes: Optional notes about the edit.

        Returns:
            The updated AttendanceRecord.

        Raises:
            AttendanceError: If record not found.
        """
        record = await self.attendance_repo.get_by_id(record_id)
        if record is None:
            raise AttendanceError("Record not found")

        if checkin_time:
            record.checkin_time = checkin_time
        if checkout_time:
            record.checkout_time = checkout_time
        if edited_by:
            record.edited_by = edited_by
        if notes:
            record.notes = notes

        # Recalculate if both times exist
        settings = await self.settings_repo.get_attendance_settings()
        if settings and record.checkout_time:
            work_hours = self._calculate_work_hours(
                record.checkin_time,
                record.checkout_time,
                settings.fixed_break_start,
                settings.fixed_break_end,
            )
            record.work_hours = Decimal(str(round(work_hours, 2)))

        # Log audit
        logger.info(
            "HR edited attendance record %s by admin %s",
            record_id,
            edited_by,
        )

        return await self.attendance_repo.update(record)

    def _calculate_late(
        self,
        actual_time: time,
        expected_time: time,
        tolerance_minutes: int,
    ) -> tuple[bool, int]:
        """Calculate if employee is late and by how many minutes.

        Args:
            actual_time: The actual check-in time.
            expected_time: The expected start time.
            tolerance_minutes: Allowed tolerance in minutes.

        Returns:
            Tuple of (is_late, late_minutes).
        """
        expected_dt = datetime.combine(date.today(), expected_time)
        actual_dt = datetime.combine(date.today(), actual_time)

        diff_minutes = int((actual_dt - expected_dt).total_seconds() / 60)

        if diff_minutes <= tolerance_minutes:
            return False, 0

        return True, diff_minutes

    def _calculate_early_leave(
        self,
        actual_time: time,
        expected_time: time,
        tolerance_minutes: int,
    ) -> tuple[bool, int]:
        """Calculate if employee left early and by how many minutes.

        Args:
            actual_time: The actual check-out time.
            expected_time: The expected end time.
            tolerance_minutes: Allowed tolerance in minutes.

        Returns:
            Tuple of (is_early, early_minutes).
        """
        expected_dt = datetime.combine(date.today(), expected_time)
        actual_dt = datetime.combine(date.today(), actual_time)

        diff_minutes = int((expected_dt - actual_dt).total_seconds() / 60)

        if diff_minutes <= tolerance_minutes:
            return False, 0

        return True, diff_minutes

    def _calculate_work_hours(
        self,
        checkin: datetime,
        checkout: datetime,
        break_start: time,
        break_end: time,
    ) -> float:
        """Calculate work hours excluding break time.

        Args:
            checkin: The check-in timestamp.
            checkout: The check-out timestamp.
            break_start: Break start time.
            break_end: Break end time.

        Returns:
            Work hours as a float.
        """
        # Total time in office
        total_minutes = (checkout - checkin).total_seconds() / 60

        # Calculate break duration (if within work hours)
        break_duration = 0
        checkin_time = checkin.time()
        checkout_time = checkout.time()

        # Break only counts if both break start and end are within work hours
        if checkin_time <= break_start and checkout_time >= break_end:
            break_minutes = (
                datetime.combine(date.today(), break_end)
                - datetime.combine(date.today(), break_start)
            ).total_seconds() / 60
            break_duration = break_minutes

        work_minutes = total_minutes - break_duration
        return max(work_minutes / 60, 0)
