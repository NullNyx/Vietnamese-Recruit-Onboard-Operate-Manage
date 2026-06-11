"""Tests for the OvertimeService.

Covers creation, cancellation, overlap detection, ownership,
and lifecycle state transitions.
"""

from __future__ import annotations

from datetime import date, time
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.employee_request.application.overtime_service import OvertimeService
from src.modules.employee_request.domain.entities import EmployeeRequest
from src.modules.employee_request.domain.enums import RequestStatus, RequestType
from src.modules.employee_request.domain.exceptions import (
    OvertimeEndBeforeStartError,
    OvertimeOverlapError,
    RequestNotCancellableError,
    RequestNotFoundError,
    RequestNotOwnedByEmployeeError,
)


@pytest.fixture
def mock_repo():
    """Create a mock EmployeeRequestRepository."""
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    """Create an OvertimeService with mocked repository."""
    return OvertimeService(repo=mock_repo)


@pytest.fixture
def employee_id():
    """Return a fixed employee UUID."""
    return uuid4()


class TestCreateOvertime:
    """Tests for create_overtime."""

    @pytest.mark.asyncio
    async def test_creates_submitted_request(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """Successfully creates an overtime request with SUBMITTED status."""
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_overtime(
            employee_id=employee_id,
            work_date=date(2026, 6, 11),
            start_time=time(18, 0),
            end_time=time(20, 30),
            reason="Project deadline",
        )

        assert result.employee_id == employee_id
        assert result.request_type == RequestType.OVERTIME
        assert result.status == RequestStatus.SUBMITTED
        assert result.work_date == date(2026, 6, 11)
        assert result.start_time == time(18, 0)
        assert result.end_time == time(20, 30)
        assert result.reason == "Project deadline"
        assert result.project_or_task is None

    @pytest.mark.asyncio
    async def test_duration_is_derived(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """Duration is computed from start/end, not user-supplied."""
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_overtime(
            employee_id=employee_id,
            work_date=date(2026, 6, 11),
            start_time=time(18, 0),
            end_time=time(20, 30),
            reason="Overtime",
        )

        # 18:00 → 20:30 = 150 minutes
        assert result.duration_minutes == 150

    @pytest.mark.asyncio
    async def test_duration_handles_midnight(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """Duration spans midnight correctly."""
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_overtime(
            employee_id=employee_id,
            work_date=date(2026, 6, 11),
            start_time=time(22, 0),
            end_time=time(1, 0),
            reason="Night shift",
        )

        # 22:00 → 01:00 (next day) = 180 minutes
        assert result.duration_minutes == 180

    @pytest.mark.asyncio
    async def test_rejects_end_before_start(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """end_time == start_time is rejected."""
        with pytest.raises(OvertimeEndBeforeStartError):
            await service.create_overtime(
                employee_id=employee_id,
                work_date=date(2026, 6, 11),
                start_time=time(18, 0),
                end_time=time(18, 0),
                reason="Invalid",
            )

    @pytest.mark.asyncio
    async def test_allows_overnight_overtime(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """end_time before start_time is treated as next-day overnight."""
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_overtime(
            employee_id=employee_id,
            work_date=date(2026, 6, 11),
            start_time=time(22, 0),
            end_time=time(2, 0),
            reason="Night shift",
        )
        # 22:00 → 02:00 next day = 240 minutes
        assert result.duration_minutes == 240

    @pytest.mark.asyncio
    async def test_blocks_overlap_with_submitted(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """Overlap with existing submitted overtime is blocked."""
        existing = MagicMock(spec=EmployeeRequest)
        existing.status = RequestStatus.SUBMITTED
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[existing])

        with pytest.raises(OvertimeOverlapError):
            await service.create_overtime(
                employee_id=employee_id,
                work_date=date(2026, 6, 11),
                start_time=time(18, 0),
                end_time=time(20, 0),
                reason="Overlap test",
            )

    @pytest.mark.asyncio
    async def test_blocks_overlap_with_approved(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """Overlap with existing approved overtime is blocked."""
        existing = MagicMock(spec=EmployeeRequest)
        existing.status = RequestStatus.APPROVED
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[existing])

        with pytest.raises(OvertimeOverlapError):
            await service.create_overtime(
                employee_id=employee_id,
                work_date=date(2026, 6, 11),
                start_time=time(18, 0),
                end_time=time(20, 0),
                reason="Overlap test",
            )

    @pytest.mark.asyncio
    async def test_allows_same_date_with_rejected(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """Same date with only rejected/cancelled requests is allowed."""
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_overtime(
            employee_id=employee_id,
            work_date=date(2026, 6, 11),
            start_time=time(18, 0),
            end_time=time(20, 0),
            reason="New request after rejection",
        )
        assert result.status == RequestStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_passes_project_or_task(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """Optional project_or_task is stored."""
        mock_repo.find_overlapping_overtime = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_overtime(
            employee_id=employee_id,
            work_date=date(2026, 6, 11),
            start_time=time(18, 0),
            end_time=time(20, 0),
            reason="Feature work",
            project_or_task="VROOM-123",
        )
        assert result.project_or_task == "VROOM-123"


class TestCancelOvertime:
    """Tests for cancel_overtime."""

    @pytest.mark.asyncio
    async def test_cancels_own_submitted(self, service, mock_repo, employee_id):
        """Employee can cancel own submitted request."""
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = employee_id
        existing.status = RequestStatus.SUBMITTED

        mock_repo.get_by_id = AsyncMock(return_value=existing)
        mock_repo.update = AsyncMock(side_effect=lambda r: r)

        result = await service.cancel_overtime(
            request_id=request_id,
            employee_id=employee_id,
            cancellation_reason="No longer needed",
        )

        assert result.status == RequestStatus.CANCELLED
        assert result.cancellation_reason == "No longer needed"

    @pytest.mark.asyncio
    async def test_raises_not_found(self, service, mock_repo, employee_id):
        """Cancelling a non-existent request raises error."""
        request_id = uuid4()
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(RequestNotFoundError):
            await service.cancel_overtime(
                request_id=request_id,
                employee_id=employee_id,
            )

    @pytest.mark.asyncio
    async def test_raises_not_owned(self, service, mock_repo, employee_id):
        """Employee cannot cancel another employee's request."""
        request_id = uuid4()
        other_employee_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = other_employee_id  # Different employee
        existing.status = RequestStatus.SUBMITTED

        mock_repo.get_by_id = AsyncMock(return_value=existing)

        with pytest.raises(RequestNotOwnedByEmployeeError):
            await service.cancel_overtime(
                request_id=request_id,
                employee_id=employee_id,
            )

    @pytest.mark.asyncio
    async def test_raises_if_not_submitted(self, service, mock_repo, employee_id):
        """Cannot cancel a request that is not in SUBMITTED status."""
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = employee_id

        for status in [RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED]:
            existing.status = status
            mock_repo.get_by_id = AsyncMock(return_value=existing)

            with pytest.raises(RequestNotCancellableError):
                await service.cancel_overtime(
                    request_id=request_id,
                    employee_id=employee_id,
                )

    @pytest.mark.asyncio
    async def test_cancel_without_reason(self, service, mock_repo, employee_id):
        """Cancellation without a reason is allowed."""
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = employee_id
        existing.status = RequestStatus.SUBMITTED

        mock_repo.get_by_id = AsyncMock(return_value=existing)
        mock_repo.update = AsyncMock(side_effect=lambda r: r)

        result = await service.cancel_overtime(
            request_id=request_id,
            employee_id=employee_id,
        )
        assert result.status == RequestStatus.CANCELLED
        assert result.cancellation_reason is None


class TestListOvertime:
    """Tests for list_my_overtime."""

    @pytest.mark.asyncio
    async def test_returns_only_overtime_requests(
        self,
        service,
        mock_repo,
        employee_id,
    ):
        """list_my_overtime filters by request_type=overtime."""
        ot1 = MagicMock(spec=EmployeeRequest)
        ot1.request_type = RequestType.OVERTIME
        ot2 = MagicMock(spec=EmployeeRequest)
        ot2.request_type = RequestType.OVERTIME
        # Future leave request — should be excluded
        leave = MagicMock(spec=EmployeeRequest)
        leave.request_type = "leave"

        mock_repo.get_by_employee_id = AsyncMock(return_value=[ot1, leave, ot2])

        result = await service.list_my_overtime(employee_id=employee_id)
        assert len(result) == 2
        assert result == [ot1, ot2]

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, service, mock_repo, employee_id):
        """Employee with no requests gets empty list."""
        mock_repo.get_by_employee_id = AsyncMock(return_value=[])

        result = await service.list_my_overtime(employee_id=employee_id)
        assert result == []
