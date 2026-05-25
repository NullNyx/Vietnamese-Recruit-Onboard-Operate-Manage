"""Unit tests for ESSDashboardService.

Tests the dashboard aggregation logic: today's attendance status mapping,
pending request counts, monthly summary computation, and annual leave
balance retrieval.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.attendance.domain.entities import AttendanceRecord
from src.modules.attendance.domain.enums import AttendanceStatus
from src.modules.self_service.api.schemas import AttendanceStatusEnum
from src.modules.self_service.application.ess_dashboard_service import (
    ESSDashboardService,
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
    repo.get_monthly_report = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession for direct queries."""
    session = AsyncMock()
    # Default: return 0 for count queries, None for scalar queries
    mock_result = AsyncMock()
    mock_result.scalar.return_value = 0
    mock_result.scalars.return_value = AsyncMock(first=AsyncMock(return_value=None))
    session.execute = AsyncMock(return_value=mock_result)
    return session


@pytest.fixture
def service(mock_attendance_repo, mock_session):
    """Create an ESSDashboardService with mocked dependencies."""
    return ESSDashboardService(
        attendance_repo=mock_attendance_repo,
        session=mock_session,
    )


class TestGetTodayAttendanceStatus:
    """Tests for _get_today_attendance_status (attendance status mapping)."""

    async def test_no_record_returns_not_checked_in(
        self, service, mock_attendance_repo, employee_id
    ):
        """No attendance record → not_checked_in."""
        mock_attendance_repo.get_by_employee_date.return_value = None

        result = await service._get_today_attendance_status(
            employee_id, date.today()
        )

        assert result == AttendanceStatusEnum.not_checked_in

    async def test_check_in_only_returns_checked_in(
        self, service, mock_attendance_repo, employee_id
    ):
        """Record with check_in but no check_out → checked_in."""
        record = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in=datetime.now(UTC),
            check_out=None,
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = record

        result = await service._get_today_attendance_status(
            employee_id, date.today()
        )

        assert result == AttendanceStatusEnum.checked_in

    async def test_both_check_in_and_out_returns_checked_out(
        self, service, mock_attendance_repo, employee_id
    ):
        """Record with both check_in and check_out → checked_out."""
        record = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
            check_out=datetime(2024, 1, 15, 17, 0, 0, tzinfo=UTC),
            work_hours=Decimal("8.0"),
            status=AttendanceStatus.PRESENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = record

        result = await service._get_today_attendance_status(
            employee_id, date.today()
        )

        assert result == AttendanceStatusEnum.checked_out

    async def test_record_without_check_in_returns_not_checked_in(
        self, service, mock_attendance_repo, employee_id
    ):
        """Edge case: record exists but check_in is None → not_checked_in."""
        record = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in=None,
            check_out=None,
            status=AttendanceStatus.ABSENT,
        )
        mock_attendance_repo.get_by_employee_date.return_value = record

        result = await service._get_today_attendance_status(
            employee_id, date.today()
        )

        assert result == AttendanceStatusEnum.not_checked_in


class TestGetMonthlySummary:
    """Tests for _get_monthly_summary."""

    async def test_empty_records_returns_zero_summary(
        self, service, mock_attendance_repo, employee_id
    ):
        """No records → all zeros."""
        mock_attendance_repo.get_monthly_report.return_value = []

        result = await service._get_monthly_summary(employee_id, 2024, 1)

        assert result.days_worked == 0
        assert result.days_absent == 0
        assert result.total_hours == Decimal("0")

    async def test_counts_worked_days_correctly(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should count present, late, and early_leave as days_worked."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 1),
                check_in=datetime(2024, 1, 1, 8, 0, 0, tzinfo=UTC),
                work_hours=Decimal("8.0"),
                status=AttendanceStatus.PRESENT,
            ),
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 2),
                check_in=datetime(2024, 1, 2, 8, 30, 0, tzinfo=UTC),
                work_hours=Decimal("7.5"),
                status=AttendanceStatus.LATE,
            ),
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 3),
                check_in=datetime(2024, 1, 3, 8, 0, 0, tzinfo=UTC),
                work_hours=Decimal("6.0"),
                status=AttendanceStatus.EARLY_LEAVE,
            ),
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service._get_monthly_summary(employee_id, 2024, 1)

        assert result.days_worked == 3

    async def test_counts_absent_days(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should count absent status as days_absent."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 1),
                check_in=None,
                work_hours=None,
                status=AttendanceStatus.ABSENT,
            ),
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 2),
                check_in=datetime(2024, 1, 2, 8, 0, 0, tzinfo=UTC),
                work_hours=Decimal("8.0"),
                status=AttendanceStatus.PRESENT,
            ),
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service._get_monthly_summary(employee_id, 2024, 1)

        assert result.days_absent == 1
        assert result.days_worked == 1

    async def test_sums_total_hours(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should sum work_hours across all records."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, i),
                check_in=datetime(2024, 1, i, 8, 0, 0, tzinfo=UTC),
                work_hours=Decimal("8.0"),
                status=AttendanceStatus.PRESENT,
            )
            for i in range(1, 4)
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service._get_monthly_summary(employee_id, 2024, 1)

        assert result.total_hours == Decimal("24.0")

    async def test_handles_none_work_hours(
        self, service, mock_attendance_repo, employee_id
    ):
        """Should treat None work_hours as 0."""
        records = [
            AttendanceRecord(
                id=uuid4(),
                employee_id=employee_id,
                work_date=date(2024, 1, 1),
                check_in=datetime(2024, 1, 1, 8, 0, 0, tzinfo=UTC),
                work_hours=None,
                status=AttendanceStatus.PRESENT,
            ),
        ]
        mock_attendance_repo.get_monthly_report.return_value = records

        result = await service._get_monthly_summary(employee_id, 2024, 1)

        assert result.total_hours == Decimal("0")


class TestGetDashboard:
    """Tests for the full get_dashboard aggregation."""

    async def test_returns_complete_dashboard_response(
        self, service, mock_attendance_repo, mock_session, employee_id
    ):
        """Should return a complete ESSDashboardResponse with all fields."""
        from unittest.mock import MagicMock

        # Setup: no attendance record, no pending requests, no balance
        mock_attendance_repo.get_by_employee_date.return_value = None
        mock_attendance_repo.get_monthly_report.return_value = []

        # Mock session.execute to return 0 for counts and None for balance lookups
        # Use MagicMock for .scalars() since it's a sync method on the result
        async def mock_execute(stmt):
            result = MagicMock()
            result.scalar.return_value = 0
            scalars_mock = MagicMock()
            scalars_mock.first.return_value = None
            result.scalars.return_value = scalars_mock
            return result

        mock_session.execute = AsyncMock(side_effect=mock_execute)

        result = await service.get_dashboard(employee_id)

        assert result.today_attendance == AttendanceStatusEnum.not_checked_in
        assert result.pending_leave_count == 0
        assert result.pending_overtime_count == 0
        assert result.monthly_summary.days_worked == 0
        assert result.monthly_summary.days_absent == 0
        assert result.monthly_summary.total_hours == Decimal("0")
        assert result.annual_leave_remaining is None
