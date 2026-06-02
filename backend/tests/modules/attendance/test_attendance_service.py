"""Unit tests for AttendanceService — check-in, check-out, and HR edit.

Tests cover:
- Basic check-in and check-out
- Late detection
- Early leave detection
- Work hours calculation
- IP whitelist validation
- HR record editing
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.modules.attendance.application.attendance_service import (
    AttendanceService,
    CheckinError,
    CheckoutError,
)
from src.modules.attendance.domain.entities import (
    AttendanceRecord,
    AttendanceSettings,
)


class TestCheckin:
    """Tests for check-in functionality."""

    @pytest.mark.asyncio
    async def test_checkin_success(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-in should succeed with valid data."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings
        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        employee_id = uuid4()
        timestamp = datetime.now(UTC)

        result = await service.checkin(employee_id, timestamp)

        assert result is not None
        assert result.employee_id == employee_id
        assert result.checkin_time == timestamp
        assert result.source == "web"
        mock_attendance_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_checkin_late(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-in after tolerance should be marked as late."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings
        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        employee_id = uuid4()
        # Check in at 08:25 (15 minutes late, tolerance is 10)
        timestamp = datetime.combine(date.today(), time(8, 25)).replace(tzinfo=UTC)

        result = await service.checkin(employee_id, timestamp)

        assert result.is_late is True
        assert result.late_minutes >= 10  # At least tolerance

    @pytest.mark.asyncio
    async def test_checkin_within_tolerance(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-in within tolerance should not be marked as late."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings
        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        employee_id = uuid4()
        # Check in at 08:05 (5 minutes late, tolerance is 10)
        timestamp = datetime.combine(date.today(), time(8, 5)).replace(tzinfo=UTC)

        result = await service.checkin(employee_id, timestamp)

        assert result.is_late is False
        assert result.late_minutes == 0

    @pytest.mark.asyncio
    async def test_checkin_already_checked_in(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-in should fail if already checked in today."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings
        existing = AttendanceRecord(
            employee_id=uuid4(),
            checkin_time=datetime.now(UTC),
            checkout_time=None,
        )
        mock_attendance_repo.get_by_employee_and_date.return_value = existing

        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        with pytest.raises(CheckinError, match="Already checked in"):
            await service.checkin(existing.employee_id, datetime.now(UTC))

    @pytest.mark.asyncio
    async def test_checkin_ip_whitelist(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-in should fail if IP not in whitelist."""
        default_attendance_settings.ip_whitelist_enabled = True
        default_attendance_settings.ip_whitelist = "192.168.1.100,10.0.0.50"
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings

        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        with pytest.raises(CheckinError, match="not in whitelist"):
            await service.checkin(
                uuid4(),
                datetime.now(UTC),
                ip_address="192.168.1.200",
            )

    @pytest.mark.asyncio
    async def test_checkin_web_disabled(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-in should fail if web check-in is disabled."""
        default_attendance_settings.checkin_web_enabled = False
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings

        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        with pytest.raises(CheckinError, match="Web check-in is disabled"):
            await service.checkin(uuid4(), datetime.now(UTC))


class TestCheckout:
    """Tests for check-out functionality."""

    @pytest.mark.asyncio
    async def test_checkout_success(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-out should calculate work hours correctly."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings

        checkin_time = datetime.combine(date.today(), time(8, 0)).replace(tzinfo=UTC)
        checkout_time = datetime.combine(date.today(), time(17, 0)).replace(tzinfo=UTC)

        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=uuid4(),
            checkin_time=checkin_time,
            checkout_time=None,
        )
        mock_attendance_repo.get_by_employee_and_date.return_value = existing

        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        result = await service.checkout(existing.employee_id, checkout_time)

        assert result.checkout_time == checkout_time
        assert result.work_hours == Decimal("8.00")  # 9 hours - 1 hour break
        assert result.is_early_leave is False

    @pytest.mark.asyncio
    async def test_checkout_early(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-out before end time should be marked as early leave."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings

        checkin_time = datetime.combine(date.today(), time(8, 0)).replace(tzinfo=UTC)
        checkout_time = datetime.combine(date.today(), time(16, 0)).replace(tzinfo=UTC)

        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=uuid4(),
            checkin_time=checkin_time,
            checkout_time=None,
        )
        mock_attendance_repo.get_by_employee_and_date.return_value = existing

        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        result = await service.checkout(existing.employee_id, checkout_time)

        assert result.is_early_leave is True
        assert result.early_minutes == 60  # 1 hour early

    @pytest.mark.asyncio
    async def test_checkout_no_checkin(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """Check-out should fail if no check-in record exists."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings
        mock_attendance_repo.get_by_employee_and_date.return_value = None

        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        with pytest.raises(CheckoutError, match="No check-in record"):
            await service.checkout(uuid4(), datetime.now(UTC))


class TestWorkHoursCalculation:
    """Tests for work hours calculation."""

    def test_work_hours_with_break(self):
        """Work hours should subtract break time."""
        from src.modules.attendance.application.attendance_service import AttendanceService

        service = AttendanceService.__new__(AttendanceService)

        checkin = datetime.combine(date.today(), time(8, 0))
        checkout = datetime.combine(date.today(), time(17, 0))
        break_start = time(12, 0)
        break_end = time(13, 0)

        hours = service._calculate_work_hours(checkin, checkout, break_start, break_end)

        assert hours == 8.0  # 9 hours total - 1 hour break = 8 hours

    def test_work_hours_without_break(self):
        """Work hours should not subtract break if outside break window."""
        from src.modules.attendance.application.attendance_service import AttendanceService

        service = AttendanceService.__new__(AttendanceService)

        checkin = datetime.combine(date.today(), time(6, 0))
        checkout = datetime.combine(date.today(), time(14, 0))
        break_start = time(12, 0)
        break_end = time(13, 0)

        hours = service._calculate_work_hours(checkin, checkout, break_start, break_end)

        # Break is not fully within work hours, so no break deduction
        assert hours == 7.0  # 8 hours - 1 hour partial break

    def test_work_hours_short_day(self):
        """Work hours for a short work day."""
        from src.modules.attendance.application.attendance_service import AttendanceService

        service = AttendanceService.__new__(AttendanceService)

        checkin = datetime.combine(date.today(), time(9, 0))
        checkout = datetime.combine(date.today(), time(12, 0))
        break_start = time(12, 0)
        break_end = time(13, 0)

        hours = service._calculate_work_hours(checkin, checkout, break_start, break_end)

        assert hours == 3.0


class TestHREditRecord:
    """Tests for HR manual record editing."""

    @pytest.mark.asyncio
    async def test_hr_edit_checkin_time(self, mock_attendance_repo, mock_settings_repo, default_attendance_settings):
        """HR should be able to edit check-in time."""
        mock_settings_repo.get_attendance_settings.return_value = default_attendance_settings

        original_time = datetime.combine(date.today(), time(8, 30)).replace(tzinfo=UTC)
        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=uuid4(),
            checkin_time=original_time,
            checkout_time=None,
        )
        mock_attendance_repo.get_by_id.return_value = existing

        service = AttendanceService(mock_attendance_repo, mock_settings_repo)

        new_time = datetime.combine(date.today(), time(8, 0)).replace(tzinfo=UTC)
        result = await service.hr_edit_record(
            existing.id,
            checkin_time=new_time,
            edited_by=uuid4(),
        )

        assert result.checkin_time == new_time
        mock_attendance_repo.update.assert_called_once()
