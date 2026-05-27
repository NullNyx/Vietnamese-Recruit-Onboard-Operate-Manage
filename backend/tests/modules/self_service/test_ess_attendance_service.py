"""Unit tests for ESSAttendanceService.

Tests self-service attendance operations: get_today_status, check_in,
check_out, and get_history with monthly summary calculation.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.attendance.domain.entities import AttendanceRecord, WorkSchedule
from src.modules.attendance.domain.enums import AttendanceStatus
from src.modules.self_service.application.ess_attendance_service import (
    ESSAttendanceService,
)


@pytest.fixture
def employee_id():
    """Generate a fixed employee UUID for tests."""
    return uuid4()


@pytest.fixture
def mock_attendance_repo():
    """Create a mock AttendanceRepository."""
    repo = AsyncMock()
    repo.get_by_employee_date = AsyncMock(return_value=None)
    repo.create = AsyncMock(side_effect=lambda r: r)
    repo.update = AsyncMock(side_effect=lambda r: r)
    repo.get_monthly_report = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_schedule_repo():
    """Create a mock ScheduleRepository with a default schedule."""
    repo = AsyncMock()
    schedule = WorkSchedule(
        id=uuid4(),
        name="Default",
        start_time=time(8, 0),
        end_time=time(17, 0),
        break_minutes=60,
        late_threshold_minutes=15,
        early_leave_threshold_minutes=15,
        is_default=True,
    )
    repo.get_default = AsyncMock(return_value=schedule)
    return repo


@pytest.fixture
def service(mock_attendance_repo, mock_schedule_repo):
    """Create an ESSAttendanceService with mocked dependencies."""
    return ESSAttendanceService(
        attendance_repo=mock_attendance_repo,
        schedule_repo=mock_schedule_repo,
    )


class TestGetTodayStatus:
    """Tests for get_today_status."""

    async def test_returns_none_when_no_record(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should return None when no attendance record exists for today."""
        mock_attendance_repo.get_by_employee_date.return_value = None

        result = await service.get_today_status(employee_id)

        assert result is None

    async def test_returns_record_when_exists(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should return the attendance record when one exists for today."""
        record = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in=datetime.now(UTC),
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = record

        result = await service.get_today_status(employee_id)

        assert result == record
        assert result.employee_id == employee_id

    async def test_queries_with_today_date(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should query the repository with today's date."""
        await service.get_today_status(employee_id)

        mock_attendance_repo.get_by_employee_date.assert_called_once()
        call_args = mock_attendance_repo.get_by_employee_date.call_args
        assert call_args[0][0] == employee_id
        assert call_args[0][1] == datetime.now(UTC).date()


class TestCheckIn:
    """Tests for check_in."""

    async def test_creates_record_on_first_checkin(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should create a new attendance record with check_in timestamp."""
        mock_attendance_repo.get_by_employee_date.return_value = None

        result = await service.check_in(employee_id)

        assert result.employee_id == employee_id
        assert result.check_in is not None
        assert result.work_date == datetime.now(UTC).date()
        mock_attendance_repo.create.assert_called_once()

    async def test_rejects_duplicate_checkin_with_409(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should raise HTTPException 409 with ALREADY_CHECKED_IN code."""
        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in=datetime.now(UTC),
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = existing

        with pytest.raises(HTTPException) as exc_info:
            await service.check_in(employee_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "ALREADY_CHECKED_IN"

    async def test_sets_status_present_when_on_time(
        self, service, mock_attendance_repo, mock_schedule_repo, employee_id
    ):
        """Should set status to 'present' when check-in is before late threshold."""
        mock_attendance_repo.get_by_employee_date.return_value = None

        # Patch datetime.now to return a time before the threshold (8:00 + 15min = 8:15)
        early_time = datetime(2024, 1, 15, 8, 10, 0, tzinfo=UTC)
        with patch(
            "src.modules.self_service.application.ess_attendance_service.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = early_time
            mock_dt.combine = datetime.combine
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = await service.check_in(employee_id)

        assert result.status == AttendanceStatus.PRESENT

    async def test_sets_status_late_when_after_threshold(
        self, service, mock_attendance_repo, mock_schedule_repo, employee_id
    ):
        """Should set status to 'late' when check-in is after late threshold."""
        mock_attendance_repo.get_by_employee_date.return_value = None

        # Patch datetime.now to return a time after the threshold (8:00 + 15min = 8:15)
        late_time = datetime(2024, 1, 15, 8, 30, 0, tzinfo=UTC)
        with patch(
            "src.modules.self_service.application.ess_attendance_service.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = late_time
            mock_dt.combine = datetime.combine
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = await service.check_in(employee_id)

        assert result.status == AttendanceStatus.LATE

    async def test_sets_present_when_no_schedule(
        self, service, mock_attendance_repo, mock_schedule_repo, employee_id
    ):
        """Should default to 'present' status when no schedule is configured."""
        mock_attendance_repo.get_by_employee_date.return_value = None
        mock_schedule_repo.get_default.return_value = None

        result = await service.check_in(employee_id)

        assert result.status == AttendanceStatus.PRESENT
        assert result.schedule_id is None


class TestCheckOut:
    """Tests for check_out."""

    async def test_updates_record_with_checkout_time(
        self, service, mock_attendance_repo, mock_schedule_repo, employee_id
    ):
        """Should update the record with check_out timestamp and work_hours."""
        check_in_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date(2024, 1, 15),
            check_in=check_in_time,
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = existing

        checkout_time = datetime(2024, 1, 15, 17, 0, 0, tzinfo=UTC)
        with patch(
            "src.modules.self_service.application.ess_attendance_service.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = checkout_time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = await service.check_out(employee_id)

        assert result.check_out == checkout_time
        assert result.work_hours is not None
        mock_attendance_repo.update.assert_called_once()

    async def test_rejects_checkout_without_checkin_409(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should raise HTTPException 409 with NOT_CHECKED_IN when no record."""
        mock_attendance_repo.get_by_employee_date.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.check_out(employee_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "NOT_CHECKED_IN"

    async def test_rejects_checkout_when_already_checked_out_409(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should raise HTTPException 409 with ALREADY_CHECKED_OUT."""
        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in=datetime.now(UTC) - timedelta(hours=8),
            check_out=datetime.now(UTC),
            work_hours=Decimal("7.00"),
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = existing

        with pytest.raises(HTTPException) as exc_info:
            await service.check_out(employee_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "ALREADY_CHECKED_OUT"

    async def test_rejects_checkout_when_record_has_no_checkin(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should raise 409 NOT_CHECKED_IN when record exists but check_in is None."""
        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in=None,
            status=AttendanceStatus.ABSENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = existing

        with pytest.raises(HTTPException) as exc_info:
            await service.check_out(employee_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "NOT_CHECKED_IN"

    async def test_calculates_work_hours_correctly(
        self, service, mock_attendance_repo, mock_schedule_repo, employee_id
    ):
        """Should calculate work_hours = (checkout - checkin) - break_minutes."""
        # 8 hours total - 1 hour break = 7 hours
        check_in_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date(2024, 1, 15),
            check_in=check_in_time,
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = existing

        checkout_time = datetime(2024, 1, 15, 16, 0, 0, tzinfo=UTC)
        with patch(
            "src.modules.self_service.application.ess_attendance_service.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = checkout_time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = await service.check_out(employee_id)

        # 8 hours - 1 hour break = 7 hours
        assert result.work_hours == Decimal("7.0")

    async def test_work_hours_minimum_zero(
        self, service, mock_attendance_repo, mock_schedule_repo, employee_id
    ):
        """Should clamp work_hours to minimum 0 when break exceeds work time."""
        # 30 minutes total - 60 minutes break = negative → clamped to 0
        check_in_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
        existing = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date(2024, 1, 15),
            check_in=check_in_time,
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = existing

        checkout_time = datetime(2024, 1, 15, 8, 30, 0, tzinfo=UTC)
        with patch(
            "src.modules.self_service.application.ess_attendance_service.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = checkout_time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = await service.check_out(employee_id)

        assert result.work_hours == Decimal("0")


class TestGetHistory:
    """Tests for get_history."""

    async def test_returns_records_and_summary(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should return records list and computed summary."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, i),
                check_in=datetime(2024, 1, i, 8, 0, 0, tzinfo=UTC),
                check_out=datetime(2024, 1, i, 17, 0, 0, tzinfo=UTC),
                work_hours=Decimal("8.0"),
                overtime_hours=Decimal("0"),
                status=AttendanceStatus.PRESENT,
            )
            for i in range(1, 4)
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service.get_history(employee_id, month=1, year=2024)

        assert result["records"] == records
        assert result["summary"]["total_work_days"] == 3
        assert result["summary"]["total_work_hours"] == Decimal("24.0")
        assert result["summary"]["total_overtime_hours"] == Decimal("0")
        assert result["summary"]["late_count"] == 0
        assert result["summary"]["early_departure_count"] == 0

    async def test_summary_counts_late_arrivals(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should count late arrivals in the summary."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 1),
                check_in=datetime(2024, 1, 1, 8, 30, 0, tzinfo=UTC),
                check_out=datetime(2024, 1, 1, 17, 0, 0, tzinfo=UTC),
                work_hours=Decimal("7.5"),
                overtime_hours=Decimal("0"),
                status=AttendanceStatus.LATE,
            ),
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 2),
                check_in=datetime(2024, 1, 2, 8, 0, 0, tzinfo=UTC),
                check_out=datetime(2024, 1, 2, 17, 0, 0, tzinfo=UTC),
                work_hours=Decimal("8.0"),
                overtime_hours=Decimal("0"),
                status=AttendanceStatus.PRESENT,
            ),
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service.get_history(employee_id, month=1, year=2024)

        assert result["summary"]["late_count"] == 1
        assert result["summary"]["total_work_days"] == 2

    async def test_summary_counts_early_departures(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should count early departures in the summary."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 1),
                check_in=datetime(2024, 1, 1, 8, 0, 0, tzinfo=UTC),
                check_out=datetime(2024, 1, 1, 15, 0, 0, tzinfo=UTC),
                work_hours=Decimal("6.0"),
                overtime_hours=Decimal("0"),
                status=AttendanceStatus.EARLY_LEAVE,
            ),
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service.get_history(employee_id, month=1, year=2024)

        assert result["summary"]["early_departure_count"] == 1
        assert result["summary"]["total_work_days"] == 1

    async def test_empty_month_returns_zero_summary(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should return zero summary when no records exist for the month."""
        mock_attendance_repo.get_monthly_report.return_value = []

        result = await service.get_history(employee_id, month=6, year=2024)

        assert result["records"] == []
        assert result["summary"]["total_work_days"] == 0
        assert result["summary"]["total_work_hours"] == Decimal("0")
        assert result["summary"]["total_overtime_hours"] == Decimal("0")
        assert result["summary"]["late_count"] == 0
        assert result["summary"]["early_departure_count"] == 0

    async def test_queries_repo_with_correct_params(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should pass employee_id, year, and month to the repository."""
        await service.get_history(employee_id, month=3, year=2024)

        mock_attendance_repo.get_monthly_report.assert_called_once_with(
            employee_id, 2024, 3
        )

    async def test_summary_includes_overtime_hours(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should sum overtime_hours across all records."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 1),
                check_in=datetime(2024, 1, 1, 8, 0, 0, tzinfo=UTC),
                check_out=datetime(2024, 1, 1, 19, 0, 0, tzinfo=UTC),
                work_hours=Decimal("10.0"),
                overtime_hours=Decimal("2.0"),
                status=AttendanceStatus.PRESENT,
            ),
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 2),
                check_in=datetime(2024, 1, 2, 8, 0, 0, tzinfo=UTC),
                check_out=datetime(2024, 1, 2, 18, 0, 0, tzinfo=UTC),
                work_hours=Decimal("9.0"),
                overtime_hours=Decimal("1.0"),
                status=AttendanceStatus.PRESENT,
            ),
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service.get_history(employee_id, month=1, year=2024)

        assert result["summary"]["total_overtime_hours"] == Decimal("3.0")


class TestCalculateWorkHours:
    """Tests for the static _calculate_work_hours method."""

    def test_standard_8_hour_day(self):
        """8 hours minus 60 min break = 7 hours."""
        check_in = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
        check_out = datetime(2024, 1, 15, 16, 0, 0, tzinfo=UTC)

        result = ESSAttendanceService._calculate_work_hours(check_in, check_out, 60)

        assert result == Decimal("7.0")

    def test_minimum_zero(self):
        """Should return 0 when break exceeds work time."""
        check_in = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
        check_out = datetime(2024, 1, 15, 8, 30, 0, tzinfo=UTC)

        result = ESSAttendanceService._calculate_work_hours(check_in, check_out, 60)

        assert result == Decimal("0")

    def test_no_break(self):
        """Should return full hours when break_minutes is 0."""
        check_in = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
        check_out = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        result = ESSAttendanceService._calculate_work_hours(check_in, check_out, 0)

        assert result == Decimal("4.0")

    def test_partial_hours(self):
        """Should handle partial hours correctly."""
        check_in = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
        check_out = datetime(2024, 1, 15, 12, 30, 0, tzinfo=UTC)

        result = ESSAttendanceService._calculate_work_hours(check_in, check_out, 30)

        assert result == Decimal("4.0")
