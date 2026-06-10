"""Application service for Employee-owned Attendance operations.

Handles check-in/check-out logic with idempotent, no-overwrite semantics.
Work date is derived from Organization timezone; timestamps stored in UTC.
"""

from datetime import UTC, date, datetime
from calendar import monthrange
from uuid import UUID
from zoneinfo import ZoneInfo

from src.modules.attendance.application.attendance_settings_service import (
    AttendanceSettingsService,
)
from src.modules.attendance.domain.entities import AttendanceRecord
from src.modules.attendance.domain.exceptions import (
    NotCheckedInError,
    OfficeNetworkRequiredError,
)
from src.modules.attendance.infrastructure.attendance_record_repository import (
    AttendanceRecordRepository,
)
from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)


class AttendanceService:
    """Service for employee-owned attendance check-in/check-out.

    Attributes:
        attendance_repo: Repository for AttendanceRecord persistence.
        org_settings_repo: Repository for Organization settings (timezone).
        settings_service: Service for office network allowlist.
    """

    def __init__(
        self,
        attendance_repo: AttendanceRecordRepository,
        org_settings_repo: OrganizationSettingsRepository,
        settings_service: AttendanceSettingsService,
    ) -> None:
        self._attendance_repo = attendance_repo
        self._org_settings_repo = org_settings_repo
        self._settings_service = settings_service

    async def _get_work_date(self) -> date:
        """Get current work date from Organization timezone.

        Returns:
            The current date in the Organization's timezone.
        """
        timezone_str = await self._org_settings_repo.get_timezone()
        tz = ZoneInfo(timezone_str)
        return datetime.now(UTC).astimezone(tz=tz).date()

    async def check_in(
        self,
        employee_id: UUID,
        client_ip: str,
        user_agent: str | None,
    ) -> AttendanceRecord:
        """Check in an employee for today.

        Idempotent: returns existing record if already checked in today.

        Args:
            employee_id: The ID of the employee checking in.
            client_ip: The client IP address.
            user_agent: The HTTP user agent string.

        Returns:
            The AttendanceRecord (created or existing).

        Raises:
            OfficeNetworkRequiredError: If IP not in office network allowlist.
        """
        # Validate IP before any DB write
        is_allowed = await self._settings_service.is_ip_allowed(client_ip)
        if not is_allowed:
            raise OfficeNetworkRequiredError()

        work_date = await self._get_work_date()
        now = datetime.now(UTC)

        # Atomic upsert: PostgreSQL ON CONFLICT DO NOTHING handles
        # the race where two concurrent requests try to check in
        # for the same employee + work_date simultaneously.
        return await self._attendance_repo.upsert_check_in(
            employee_id=employee_id,
            work_date=work_date,
            check_in_at=now,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def check_out(
        self,
        employee_id: UUID,
        client_ip: str,
        user_agent: str | None,
    ) -> AttendanceRecord:
        """Check out an employee for today.

        Idempotent: returns existing record if already checked out today.
        Requires check_in_at to be set.

        Args:
            employee_id: The ID of the employee checking out.
            client_ip: The client IP address.
            user_agent: The HTTP user agent string.

        Returns:
            The AttendanceRecord (created or existing).

        Raises:
            OfficeNetworkRequiredError: If IP not in office network allowlist.
            NotCheckedInError: If employee has not checked in today.
        """
        # Validate IP before any DB write
        is_allowed = await self._settings_service.is_ip_allowed(client_ip)
        if not is_allowed:
            raise OfficeNetworkRequiredError()

        work_date = await self._get_work_date()

        # Get existing record
        existing = await self._attendance_repo.get_by_employee_and_date(employee_id, work_date)

        if existing is None:
            raise NotCheckedInError()

        if existing.check_in_at is None:
            raise NotCheckedInError()

        # Idempotent - if already checked out, return existing
        if existing.check_out_at is not None:
            return existing

        # Update with check-out
        now = datetime.now(UTC)
        existing.check_out_at = now
        existing.check_out_ip = client_ip
        existing.check_out_user_agent = user_agent
        return await self._attendance_repo.update(existing)

    async def get_today(self, employee_id: UUID) -> AttendanceRecord | None:
        """Get today's attendance record for an employee.

        Args:
            employee_id: The ID of the employee.

        Returns:
            The AttendanceRecord if exists for today, None otherwise.
        """
        work_date = await self._get_work_date()
        return await self._attendance_repo.get_by_employee_and_date(employee_id, work_date)

    async def get_history(
        self,
        employee_id: UUID,
        year: int,
        month: int,
    ) -> list[AttendanceRecord]:
        """Get attendance records for an employee in a given month.

        Args:
            employee_id: The ID of the employee.
            year: The year (e.g., 2026).
            month: The month (1-12).

        Returns:
            List of AttendanceRecord for the specified month.
        """
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        return await self._attendance_repo.get_by_employee_and_date_range(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )
