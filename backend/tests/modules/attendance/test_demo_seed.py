"""Tests for the attendance demo seed function.

Covers idempotency, active-only employee filtering, and config gating.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.bootstrap.demo_data import seed_demo_attendance


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add_all = MagicMock()
    return session


@pytest.fixture
def mock_active_employee():
    """Return a minimal active employee stub."""
    emp = MagicMock()
    emp.id = uuid4()
    emp.is_active = True
    return emp


@pytest.fixture
def mock_inactive_employee():
    """Return a minimal inactive employee stub."""
    emp = MagicMock()
    emp.id = uuid4()
    emp.is_active = False
    return emp


class TestSeedDemoAttendance:
    """Tests for seed_demo_attendance function."""

    async def _setup_count_query(self, session, model, count: int):
        """Configure session.execute to return a scalar count for the model."""

        async def side_effect(*args, **kwargs):
            # First call is the count query for AttendanceRecord
            scalar_result = MagicMock()
            scalar_result.scalar_one.return_value = count
            return scalar_result

        session.execute.side_effect = side_effect

    async def _setup_employee_query(self, session, employees: list):
        """Configure session.execute after the count to return employees."""

        async def side_effect(*args, **kwargs):
            # Mark that this is the employee query
            scalar_result = MagicMock()
            scalars_part = MagicMock()
            scalars_part.all.return_value = employees
            scalar_result.scalars.return_value = scalars_part
            return scalar_result

        session.execute.side_effect = side_effect

    @pytest.mark.asyncio
    async def test_skips_when_disabled_by_config(self, mock_session, monkeypatch):
        """Seed returns False when auto_seed_sample_data is False."""
        monkeypatch.setattr(
            "src.modules.identity.infrastructure.config.AuthSettings",
            lambda: MagicMock(auto_seed_sample_data=False),
        )
        result = await seed_demo_attendance(mock_session)
        assert result is False

    @pytest.mark.asyncio
    async def test_skips_when_records_exist(self, mock_session, monkeypatch, mock_active_employee):
        """Seed returns False when records exist for the target week."""
        monkeypatch.setattr(
            "src.modules.identity.infrastructure.config.AuthSettings",
            lambda: MagicMock(auto_seed_sample_data=True),
        )

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # Employee query → return active employees
                scalars = MagicMock()
                scalars.all.return_value = [mock_active_employee]
                result.scalars.return_value = scalars
            else:
                # Count query → return > 0
                result.scalar_one.return_value = 4
            return result

        mock_session.execute.side_effect = side_effect

        result = await seed_demo_attendance(mock_session)
        assert result is False

    @pytest.mark.asyncio
    async def test_skips_when_no_active_employees(self, mock_session, monkeypatch):
        """Seed returns False when no active employees exist."""
        monkeypatch.setattr(
            "src.modules.identity.infrastructure.config.AuthSettings",
            lambda: MagicMock(auto_seed_sample_data=True),
        )

        # Employee query returns empty list → skip immediately, no count query.
        async def side_effect(*args, **kwargs):
            result = MagicMock()
            scalars = MagicMock()
            scalars.all.return_value = []
            result.scalars.return_value = scalars
            return result

        mock_session.execute.side_effect = side_effect

        result = await seed_demo_attendance(mock_session)
        assert result is False

    @pytest.mark.asyncio
    async def test_skips_inactive_employees(
        self,
        mock_session,
        monkeypatch,
        mock_active_employee,
        mock_inactive_employee,
    ):
        """Seed does not create records for inactive employees."""
        monkeypatch.setattr(
            "src.modules.identity.infrastructure.config.AuthSettings",
            lambda: MagicMock(auto_seed_sample_data=True),
        )

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # Employee query: mock simulates SQL WHERE is_active.is_(True)
                # Only active employee returned; inactive employee filtered out
                scalars = MagicMock()
                scalars.all.return_value = [mock_active_employee]
                result.scalars.return_value = scalars
            else:
                # Count query → return 0 (no existing records)
                result.scalar_one.return_value = 0
            return result

        mock_session.execute.side_effect = side_effect

        result = await seed_demo_attendance(mock_session)
        assert result is True
        mock_session.add_all.assert_called_once()
        added_records = mock_session.add_all.call_args[0][0]
        # Records created only for the active employee (not inactive)
        assert len(added_records) == 4
        for record in added_records:
            assert record.employee_id == mock_active_employee.id
        # Verify the employee query included the is_active filter
        call_stmt = mock_session.execute.call_args_list[0][0][0]
        stmt_str = str(call_stmt)
        assert "is_active" in stmt_str

    @pytest.mark.asyncio
    async def test_creates_records_for_active_employees(
        self,
        mock_session,
        monkeypatch,
        mock_active_employee,
    ):
        """Seed creates attendance records for active employees."""
        monkeypatch.setattr(
            "src.modules.identity.infrastructure.config.AuthSettings",
            lambda: MagicMock(auto_seed_sample_data=True),
        )

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # Employee query → return active employees
                scalars = MagicMock()
                scalars.all.return_value = [mock_active_employee]
                result.scalars.return_value = scalars
            else:
                # Count query → return 0 (no existing records)
                result.scalar_one.return_value = 0
            return result

        mock_session.execute.side_effect = side_effect

        result = await seed_demo_attendance(mock_session)
        assert result is True
        mock_session.add_all.assert_called_once()
        # 4 records per employee (work week days with data)
        added_records = mock_session.add_all.call_args[0][0]
        assert len(added_records) == 4
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_have_correct_structure(
        self,
        mock_session,
        monkeypatch,
        mock_active_employee,
    ):
        """Each created record has correct required fields."""
        monkeypatch.setattr(
            "src.modules.identity.infrastructure.config.AuthSettings",
            lambda: MagicMock(auto_seed_sample_data=True),
        )

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # Employee query → return active employees
                scalars = MagicMock()
                scalars.all.return_value = [mock_active_employee]
                result.scalars.return_value = scalars
            else:
                # Count query → return 0 (no existing records)
                result.scalar_one.return_value = 0
            return result

        mock_session.execute.side_effect = side_effect

        result = await seed_demo_attendance(mock_session)
        assert result is True

        added_records = mock_session.add_all.call_args[0][0]
        for record in added_records:
            assert record.employee_id == mock_active_employee.id
            assert isinstance(record.work_date, date)
            assert record.check_in_at is not None
            assert record.check_in_ip == "192.168.1.100"
            assert record.source.value == "web"

        # Day 4 (last work day) has no check_out (incomplete)
        work_dates = sorted(r.work_date for r in added_records)
        incomplete = [r for r in added_records if r.check_out_at is None]
        assert len(incomplete) == 1
        assert incomplete[0].work_date == work_dates[3]
