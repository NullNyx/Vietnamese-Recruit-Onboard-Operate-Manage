"""Tests for the LeaveService.

Covers creation, cancellation, overlap detection, ownership,
validation, and lifecycle state transitions.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.employee_request.application.leave_service import LeaveService
from src.modules.employee_request.domain.entities import EmployeeRequest
from src.modules.employee_request.domain.enums import LeaveType, RequestStatus, RequestType
from src.modules.employee_request.domain.exceptions import (
    LeaveEndBeforeStartError,
    LeaveOverlapError,
    RequestNotCancellableError,
    RequestNotFoundError,
    RequestNotOwnedByEmployeeError,
)


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return LeaveService(repo=mock_repo)


@pytest.fixture
def employee_id():
    return uuid4()


class TestCreateLeave:
    """Tests for create_leave."""

    @pytest.mark.asyncio
    async def test_creates_submitted_leave(self, service, mock_repo, employee_id):
        """Successfully creates a leave request with SUBMITTED status."""
        mock_repo.find_overlapping_leave = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_leave(
            employee_id=employee_id,
            leave_type=LeaveType.ANNUAL,
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 17),
            reason="Family vacation",
        )

        assert result.employee_id == employee_id
        assert result.request_type == RequestType.LEAVE
        assert result.status == RequestStatus.SUBMITTED
        assert result.leave_type == LeaveType.ANNUAL
        assert result.start_date == date(2026, 6, 15)
        assert result.end_date == date(2026, 6, 17)
        assert result.reason == "Family vacation"

    @pytest.mark.asyncio
    async def test_supports_all_leave_types(self, service, mock_repo, employee_id):
        """All four leave types are accepted."""
        mock_repo.find_overlapping_leave = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        for lt in [
            LeaveType.ANNUAL,
            LeaveType.SICK,
            LeaveType.UNPAID,
            LeaveType.OTHER,
        ]:
            result = await service.create_leave(
                employee_id=employee_id,
                leave_type=lt,
                start_date=date(2026, 6, 15),
                end_date=date(2026, 6, 15),
                reason="A day off",
            )
            assert result.leave_type == lt

    @pytest.mark.asyncio
    async def test_single_day_leave(self, service, mock_repo, employee_id):
        """start_date == end_date is valid (single day)."""
        mock_repo.find_overlapping_leave = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_leave(
            employee_id=employee_id,
            leave_type=LeaveType.SICK,
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 15),
            reason="Doctor appointment",
        )
        assert result.start_date == result.end_date

    @pytest.mark.asyncio
    async def test_rejects_end_before_start(self, service, mock_repo, employee_id):
        """end_date before start_date is rejected."""
        with pytest.raises(LeaveEndBeforeStartError):
            await service.create_leave(
                employee_id=employee_id,
                leave_type=LeaveType.ANNUAL,
                start_date=date(2026, 6, 17),
                end_date=date(2026, 6, 15),
                reason="Invalid range",
            )

    @pytest.mark.asyncio
    async def test_blocks_exact_overlap(self, service, mock_repo, employee_id):
        """Exact same date range overlap is blocked."""
        mock_repo.find_overlapping_leave = AsyncMock(
            return_value=[MagicMock(spec=EmployeeRequest)],
        )
        with pytest.raises(LeaveOverlapError):
            await service.create_leave(
                employee_id=employee_id,
                leave_type=LeaveType.ANNUAL,
                start_date=date(2026, 6, 15),
                end_date=date(2026, 6, 17),
                reason="Overlapping",
            )

    @pytest.mark.asyncio
    async def test_blocks_partial_overlap(self, service, mock_repo, employee_id):
        """Partial date range overlap is also blocked."""
        mock_repo.find_overlapping_leave = AsyncMock(
            return_value=[MagicMock(spec=EmployeeRequest)],
        )
        with pytest.raises(LeaveOverlapError):
            await service.create_leave(
                employee_id=employee_id,
                leave_type=LeaveType.SICK,
                start_date=date(2026, 6, 16),
                end_date=date(2026, 6, 18),
                reason="Partial overlap",
            )

    @pytest.mark.asyncio
    async def test_no_overlap_with_rejected(self, service, mock_repo, employee_id):
        """No overlap check blocks when only rejected/cancelled exist."""
        mock_repo.find_overlapping_leave = AsyncMock(return_value=[])
        mock_repo.create = AsyncMock(side_effect=lambda r: r)

        result = await service.create_leave(
            employee_id=employee_id,
            leave_type=LeaveType.ANNUAL,
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 17),
            reason="After rejection",
        )
        assert result.status == RequestStatus.SUBMITTED


class TestCancelLeave:
    """Tests for cancel_leave."""

    @pytest.mark.asyncio
    async def test_cancels_own_submitted(self, service, mock_repo, employee_id):
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = employee_id
        existing.request_type = RequestType.LEAVE
        existing.status = RequestStatus.SUBMITTED

        mock_repo.get_by_id = AsyncMock(return_value=existing)
        mock_repo.update = AsyncMock(side_effect=lambda r: r)

        result = await service.cancel_leave(
            request_id=request_id,
            employee_id=employee_id,
            cancellation_reason="No longer needed",
        )
        assert result.status == RequestStatus.CANCELLED
        assert result.cancellation_reason == "No longer needed"

    @pytest.mark.asyncio
    async def test_raises_not_found(self, service, mock_repo, employee_id):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(RequestNotFoundError):
            await service.cancel_leave(request_id=uuid4(), employee_id=employee_id)

    @pytest.mark.asyncio
    async def test_raises_not_owned(self, service, mock_repo, employee_id):
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = uuid4()
        existing.request_type = RequestType.LEAVE
        existing.status = RequestStatus.SUBMITTED

        mock_repo.get_by_id = AsyncMock(return_value=existing)
        with pytest.raises(RequestNotOwnedByEmployeeError):
            await service.cancel_leave(request_id=request_id, employee_id=employee_id)

    @pytest.mark.asyncio
    async def test_cannot_cancel_overtime(self, service, mock_repo, employee_id):
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = employee_id
        existing.request_type = RequestType.OVERTIME
        existing.status = RequestStatus.SUBMITTED

        mock_repo.get_by_id = AsyncMock(return_value=existing)
        with pytest.raises(RequestNotCancellableError):
            await service.cancel_leave(request_id=request_id, employee_id=employee_id)

    @pytest.mark.asyncio
    async def test_raises_if_not_submitted(self, service, mock_repo, employee_id):
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = employee_id
        existing.request_type = RequestType.LEAVE

        for status in [
            RequestStatus.APPROVED,
            RequestStatus.REJECTED,
            RequestStatus.CANCELLED,
        ]:
            existing.status = status
            mock_repo.get_by_id = AsyncMock(return_value=existing)
            with pytest.raises(RequestNotCancellableError):
                await service.cancel_leave(request_id=request_id, employee_id=employee_id)

    @pytest.mark.asyncio
    async def test_cancel_without_reason(self, service, mock_repo, employee_id):
        request_id = uuid4()
        existing = MagicMock(spec=EmployeeRequest)
        existing.id = request_id
        existing.employee_id = employee_id
        existing.request_type = RequestType.LEAVE
        existing.status = RequestStatus.SUBMITTED

        mock_repo.get_by_id = AsyncMock(return_value=existing)
        mock_repo.update = AsyncMock(side_effect=lambda r: r)

        result = await service.cancel_leave(request_id=request_id, employee_id=employee_id)
        assert result.status == RequestStatus.CANCELLED
        assert result.cancellation_reason is None


class TestListLeave:
    """Tests for list_my_leaves."""

    @pytest.mark.asyncio
    async def test_returns_only_leave_requests(self, service, mock_repo, employee_id):
        l1 = MagicMock(spec=EmployeeRequest)
        l1.request_type = RequestType.LEAVE
        l2 = MagicMock(spec=EmployeeRequest)
        l2.request_type = RequestType.LEAVE
        ot = MagicMock(spec=EmployeeRequest)
        ot.request_type = RequestType.OVERTIME

        mock_repo.get_by_employee_id = AsyncMock(return_value=[l1, ot, l2])

        result = await service.list_my_leaves(employee_id=employee_id)
        assert len(result) == 2
        assert result == [l1, l2]

    @pytest.mark.asyncio
    async def test_returns_empty(self, service, mock_repo, employee_id):
        mock_repo.get_by_employee_id = AsyncMock(return_value=[])
        result = await service.list_my_leaves(employee_id=employee_id)
        assert result == []
