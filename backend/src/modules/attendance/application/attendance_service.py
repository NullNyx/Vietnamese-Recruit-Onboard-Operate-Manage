"""Application service for Employee-owned Attendance operations.

Handles check-in/check-out logic with idempotent, no-overwrite semantics.
Work date is derived from Organization timezone; timestamps stored in UTC.
"""

from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from typing import Literal
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
from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.domain.entities import AuditActionType, User
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
        is_allowed = await self._settings_service.is_ip_allowed(client_ip)
        if not is_allowed:
            raise OfficeNetworkRequiredError()

        work_date = await self._get_work_date()
        now = datetime.now(UTC)

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
        is_allowed = await self._settings_service.is_ip_allowed(client_ip)
        if not is_allowed:
            raise OfficeNetworkRequiredError()

        work_date = await self._get_work_date()
        existing = await self._attendance_repo.get_by_employee_and_date(employee_id, work_date)

        if existing is None:
            raise NotCheckedInError()

        if existing.check_in_at is None:
            raise NotCheckedInError()

        if existing.check_out_at is not None:
            return existing

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
        year: int | None = None,
        month: int | None = None,
        days: int = 7,
    ) -> list[AttendanceRecord]:
        """Get attendance records for an employee.

        If year and month are provided, returns records for that month.
        Otherwise returns records for the last ``days`` days.

        Args:
            employee_id: The ID of the employee.
            year: The year (e.g., 2026).
            month: The month (1-12).
            days: Number of recent days (default 7, used when year/month not specified).

        Returns:
            List of AttendanceRecord for the specified period.
        """
        if year is not None and month is not None:
            _, last_day = monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
        else:
            work_date = await self._get_work_date()
            end_date = work_date
            start_date = work_date - timedelta(days=days - 1)
        return await self._attendance_repo.get_by_employee_and_date_range(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def list_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: UUID | None = None,
        status: Literal["checked_in", "completed"] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AttendanceRecord], int]:
        """List attendance records across employees with filters.

        Args:
            start_date: Start date for filter range.
            end_date: End date for filter range.
            employee_id: Optional filter by employee ID.
            status: Optional filter by status (checked_in, completed).
            page: Page number (1-based).
            page_size: Records per page.

        Returns:
            Tuple of (list of AttendanceRecord, total count).
        """
        return await self._attendance_repo.list_with_filters(
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    async def correct_record(
        self,
        record_id: UUID,
        check_in_at: datetime | None,
        check_out_at: datetime | None,
        correction_reason: str,
        corrected_by_user_id: UUID,
        admin: User,
        audit_service: AuditService,
    ) -> AttendanceRecord:
        """Correct an attendance record atomically with audit log.

        The correction and audit log are written within the same
        AsyncSession transaction. If either write fails, both are rolled
        back, preserving the invariant that every correction is audit-logged.

        Args:
            record_id: The ID of the record to correct.
            check_in_at: New check-in time (None to clear).
            check_out_at: New check-out time (None to clear).
            correction_reason: Required reason for the correction.
            corrected_by_user_id: The user ID of the HR admin making the correction.
            admin: The admin User performing the correction.
            audit_service: The AuditService for writing the audit log.

        Returns:
            The corrected AttendanceRecord.

        Raises:
            ValueError: If record not found or correction_reason is empty.
        """
        stripped_reason = correction_reason.strip()
        if not stripped_reason:
            raise ValueError("Correction reason is required")

        record = await self._attendance_repo.get_by_id(record_id)
        if record is None:
            raise ValueError("Attendance record not found")

        previous_check_in_at = record.check_in_at
        previous_check_out_at = record.check_out_at

        record.check_in_at = check_in_at
        record.check_out_at = check_out_at
        record.corrected_by_user_id = corrected_by_user_id
        record.corrected_at = datetime.now(UTC)
        record.correction_reason = stripped_reason
        record.previous_check_in_at = previous_check_in_at
        record.previous_check_out_at = previous_check_out_at
        record.updated_at = datetime.now(UTC)

        corrected = await self._attendance_repo.update(record)

        await audit_service.log_action(
            admin=admin,
            action_type=AuditActionType.ATTENDANCE_CORRECTION,
            details={
                "record_id": str(record_id),
                "employee_id": str(corrected.employee_id),
                "previous_check_in_at": (
                    previous_check_in_at.isoformat() if previous_check_in_at else None
                ),
                "previous_check_out_at": (
                    previous_check_out_at.isoformat() if previous_check_out_at else None
                ),
                "new_check_in_at": (
                    corrected.check_in_at.isoformat() if corrected.check_in_at else None
                ),
                "new_check_out_at": (
                    corrected.check_out_at.isoformat() if corrected.check_out_at else None
                ),
                "correction_reason": stripped_reason,
            },
        )

        return corrected
