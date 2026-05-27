"""Unit tests for ESS Schedule Router.

Tests the schedule endpoint logic: resolving employee schedule,
fetching upcoming holidays, and handling the no-schedule case.
"""

from __future__ import annotations

from datetime import date, time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.attendance.domain.entities import (
    AttendanceRecord,
    Holiday,
    WorkSchedule,
)
from src.modules.self_service.api.schedule_router import (
    _get_employee_schedule,
    _get_upcoming_holidays,
)


@pytest.fixture
def employee_id():
    """Generate a fixed employee UUID for tests."""
    return uuid4()


@pytest.fixture
def default_schedule():
    """Create a default work schedule."""
    return WorkSchedule(
        id=uuid4(),
        name="Ca hành chính",
        start_time=time(8, 0),
        end_time=time(17, 0),
        break_minutes=60,
        late_threshold_minutes=15,
        early_leave_threshold_minutes=15,
        is_default=True,
    )


@pytest.fixture
def custom_schedule():
    """Create a custom work schedule."""
    return WorkSchedule(
        id=uuid4(),
        name="Ca sáng",
        start_time=time(6, 0),
        end_time=time(14, 0),
        break_minutes=30,
        late_threshold_minutes=10,
        early_leave_threshold_minutes=10,
        is_default=False,
    )


class TestGetEmployeeSchedule:
    """Tests for _get_employee_schedule helper."""

    async def test_returns_schedule_from_attendance_record(
        self, employee_id, custom_schedule
    ):
        """Should return the schedule linked via the employee's attendance record."""
        mock_session = AsyncMock()

        # Mock the query to return the custom schedule's ID
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = custom_schedule.id
        mock_session.execute.return_value = mock_result

        with patch(
            "src.modules.self_service.api.schedule_router.ScheduleRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = custom_schedule
            mock_repo.get_default.return_value = None
            MockRepo.return_value = mock_repo

            result = await _get_employee_schedule(employee_id, mock_session)

        assert result == custom_schedule
        mock_repo.get_by_id.assert_called_once_with(custom_schedule.id)

    async def test_falls_back_to_default_when_no_attendance_schedule(
        self, employee_id, default_schedule
    ):
        """Should return the default schedule when no attendance record has a schedule_id."""
        mock_session = AsyncMock()

        # Mock the query to return None (no schedule_id in attendance records)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch(
            "src.modules.self_service.api.schedule_router.ScheduleRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_default.return_value = default_schedule
            MockRepo.return_value = mock_repo

            result = await _get_employee_schedule(employee_id, mock_session)

        assert result == default_schedule
        mock_repo.get_default.assert_called_once()

    async def test_returns_none_when_no_schedule_exists(self, employee_id):
        """Should return None when no schedule is found at all."""
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch(
            "src.modules.self_service.api.schedule_router.ScheduleRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_default.return_value = None
            MockRepo.return_value = mock_repo

            result = await _get_employee_schedule(employee_id, mock_session)

        assert result is None

    async def test_falls_back_to_default_when_schedule_id_not_found(
        self, employee_id, default_schedule
    ):
        """Should fall back to default if the schedule_id from attendance doesn't resolve."""
        mock_session = AsyncMock()

        # Mock the query to return a schedule_id that doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()
        mock_session.execute.return_value = mock_result

        with patch(
            "src.modules.self_service.api.schedule_router.ScheduleRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo.get_default.return_value = default_schedule
            MockRepo.return_value = mock_repo

            result = await _get_employee_schedule(employee_id, mock_session)

        assert result == default_schedule


class TestGetUpcomingHolidays:
    """Tests for _get_upcoming_holidays helper."""

    async def test_returns_holidays_from_today_onwards(self):
        """Should return holidays with dates >= today."""
        mock_session = AsyncMock()

        holidays = [
            Holiday(
                id=uuid4(),
                holiday_date=date(2025, 9, 2),
                name="Quốc khánh",
                is_recurring=True,
            ),
            Holiday(
                id=uuid4(),
                holiday_date=date(2025, 12, 25),
                name="Giáng sinh",
                is_recurring=True,
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = holidays
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await _get_upcoming_holidays(mock_session)

        assert len(result) == 2
        assert result[0].name == "Quốc khánh"
        assert result[1].name == "Giáng sinh"

    async def test_returns_empty_list_when_no_holidays(self):
        """Should return empty list when no upcoming holidays exist."""
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await _get_upcoming_holidays(mock_session)

        assert result == []
