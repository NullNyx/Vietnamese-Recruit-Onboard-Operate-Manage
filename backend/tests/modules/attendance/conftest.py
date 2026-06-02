"""Pytest fixtures for Attendance module tests."""

from datetime import time
from unittest.mock import AsyncMock
import pytest

from src.modules.attendance.domain.entities import (
    AttendanceRecord,
    AttendanceSettings,
)


@pytest.fixture
def mock_attendance_repo():
    """Create a mock attendance repository."""
    repo = AsyncMock()
    repo.create = AsyncMock(side_effect=lambda r: r)
    repo.update = AsyncMock(side_effect=lambda r: r)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_employee_and_date = AsyncMock(return_value=None)
    repo.list_by_employee = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_settings_repo():
    """Create a mock settings repository."""
    repo = AsyncMock()
    repo.get_attendance_settings = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def default_attendance_settings():
    """Create default attendance settings."""
    settings = AttendanceSettings(
        id=None,
        work_model="fixed",
        checkin_web_enabled=True,
        checkin_qr_enabled=True,
        checkin_device_enabled=False,
        fixed_start_time=time(8, 0),
        fixed_end_time=time(17, 0),
        fixed_break_start=time(12, 0),
        fixed_break_end=time(13, 0),
        late_tolerance_minutes=10,
        early_leave_tolerance_minutes=10,
        weekly_off_days="saturday",
        ip_whitelist_enabled=False,
        ip_whitelist=None,
    )
    return settings
