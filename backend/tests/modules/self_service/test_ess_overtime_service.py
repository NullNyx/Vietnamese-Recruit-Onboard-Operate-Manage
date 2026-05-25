"""Unit tests for the ESS Overtime Service.

Tests cover:
- get_requests: returns all overtime requests for an employee
- create_request: validates planned_hours and work_date, creates with status "pending"
- cancel_request: verifies ownership, verifies pending status, updates to "cancelled"
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from src.modules.attendance.domain.entities import OvertimeRequest
from src.modules.attendance.domain.enums import OvertimeStatus
from src.modules.self_service.application.ess_overtime_service import ESSOvertimeService
from src.modules.self_service.api.schemas import ESSOvertimeRequestCreate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def employee_id() -> UUID:
    return uuid4()


@pytest.fixture
def other_employee_id() -> UUID:
    return uuid4()


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def service(mock_session: AsyncMock) -> ESSOvertimeService:
    return ESSOvertimeService(session=mock_session)


def _make_overtime_request(
    employee_id: UUID,
    *,
    request_id: UUID | None = None,
    work_date: date | None = None,
    planned_hours: Decimal = Decimal("2.0"),
    status: str = OvertimeStatus.PENDING,
    reason: str = "Project deadline",
) -> OvertimeRequest:
    """Helper to create an OvertimeRequest instance."""
    return OvertimeRequest(
        id=request_id or uuid4(),
        employee_id=employee_id,
        work_date=work_date or date.today() + timedelta(days=1),
        planned_hours=planned_hours,
        reason=reason,
        status=status,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Tests: get_requests
# ---------------------------------------------------------------------------


class TestGetRequests:
    """Tests for ESSOvertimeService.get_requests."""

    async def test_returns_all_requests_for_employee(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should return all overtime requests for the given employee."""
        requests = [
            _make_overtime_request(employee_id),
            _make_overtime_request(employee_id),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = requests
        mock_session.execute.return_value = mock_result

        result = await service.get_requests(employee_id)

        assert result == requests
        assert len(result) == 2
        mock_session.execute.assert_called_once()

    async def test_returns_empty_list_when_no_requests(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should return empty list when employee has no overtime requests."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await service.get_requests(employee_id)

        assert result == []


# ---------------------------------------------------------------------------
# Tests: create_request
# ---------------------------------------------------------------------------


class TestCreateRequest:
    """Tests for ESSOvertimeService.create_request."""

    async def test_creates_request_with_pending_status(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should create an overtime request with status 'pending'."""
        tomorrow = date.today() + timedelta(days=1)
        data = ESSOvertimeRequestCreate(
            work_date=tomorrow,
            planned_hours=Decimal("2.0"),
            reason="Project deadline",
        )

        # Mock refresh to set the status on the request object
        async def mock_refresh(obj: OvertimeRequest) -> None:
            obj.id = uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_session.refresh.side_effect = mock_refresh

        result = await service.create_request(employee_id, data)

        assert result.employee_id == employee_id
        assert result.work_date == tomorrow
        assert result.planned_hours == Decimal("2.0")
        assert result.reason == "Project deadline"
        assert result.status == OvertimeStatus.PENDING
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_creates_request_for_today(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should allow creating a request for today (not in the past)."""
        today = date.today()
        data = ESSOvertimeRequestCreate(
            work_date=today,
            planned_hours=Decimal("1.5"),
            reason="Urgent fix",
        )

        async def mock_refresh(obj: OvertimeRequest) -> None:
            obj.id = uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_session.refresh.side_effect = mock_refresh

        result = await service.create_request(employee_id, data)

        assert result.work_date == today
        assert result.status == OvertimeStatus.PENDING

    async def test_rejects_past_work_date(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should reject request with work_date in the past (422 INVALID_WORK_DATE)."""
        yesterday = date.today() - timedelta(days=1)
        data = ESSOvertimeRequestCreate(
            work_date=yesterday,
            planned_hours=Decimal("2.0"),
            reason="Late submission",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(employee_id, data)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_WORK_DATE"

    async def test_rejects_planned_hours_below_minimum(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should reject request with planned_hours < 0.5 (422 INVALID_PLANNED_HOURS)."""
        tomorrow = date.today() + timedelta(days=1)
        # Bypass Pydantic validation by creating object directly
        data = MagicMock()
        data.work_date = tomorrow
        data.planned_hours = Decimal("0.3")
        data.reason = "Too few hours"

        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(employee_id, data)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_PLANNED_HOURS"

    async def test_rejects_planned_hours_above_maximum(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should reject request with planned_hours > 4.0 (422 INVALID_PLANNED_HOURS)."""
        tomorrow = date.today() + timedelta(days=1)
        data = MagicMock()
        data.work_date = tomorrow
        data.planned_hours = Decimal("5.0")
        data.reason = "Too many hours"

        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(employee_id, data)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_PLANNED_HOURS"

    async def test_accepts_minimum_planned_hours(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should accept planned_hours = 0.5 (boundary)."""
        tomorrow = date.today() + timedelta(days=1)
        data = ESSOvertimeRequestCreate(
            work_date=tomorrow,
            planned_hours=Decimal("0.5"),
            reason="Minimum OT",
        )

        async def mock_refresh(obj: OvertimeRequest) -> None:
            obj.id = uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_session.refresh.side_effect = mock_refresh

        result = await service.create_request(employee_id, data)
        assert result.planned_hours == Decimal("0.5")

    async def test_accepts_maximum_planned_hours(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should accept planned_hours = 4.0 (boundary)."""
        tomorrow = date.today() + timedelta(days=1)
        data = ESSOvertimeRequestCreate(
            work_date=tomorrow,
            planned_hours=Decimal("4.0"),
            reason="Maximum OT",
        )

        async def mock_refresh(obj: OvertimeRequest) -> None:
            obj.id = uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_session.refresh.side_effect = mock_refresh

        result = await service.create_request(employee_id, data)
        assert result.planned_hours == Decimal("4.0")


# ---------------------------------------------------------------------------
# Tests: cancel_request
# ---------------------------------------------------------------------------


class TestCancelRequest:
    """Tests for ESSOvertimeService.cancel_request."""

    async def test_cancels_pending_request(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should cancel a pending request owned by the employee."""
        request_id = uuid4()
        request = _make_overtime_request(
            employee_id, request_id=request_id, status=OvertimeStatus.PENDING
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = request
        mock_session.execute.return_value = mock_result

        async def mock_refresh(obj: OvertimeRequest) -> None:
            pass  # status already set

        mock_session.refresh.side_effect = mock_refresh

        result = await service.cancel_request(employee_id, request_id)

        assert result.status == "cancelled"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_rejects_cancel_for_non_owned_request(
        self,
        service: ESSOvertimeService,
        mock_session: AsyncMock,
        employee_id: UUID,
        other_employee_id: UUID,
    ) -> None:
        """Should return 403 RESOURCE_FORBIDDEN when request belongs to another employee."""
        request_id = uuid4()
        request = _make_overtime_request(
            other_employee_id, request_id=request_id, status=OvertimeStatus.PENDING
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = request
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(employee_id, request_id)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "RESOURCE_FORBIDDEN"

    async def test_rejects_cancel_for_approved_request(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should return 409 INVALID_STATUS_TRANSITION for approved requests."""
        request_id = uuid4()
        request = _make_overtime_request(
            employee_id, request_id=request_id, status=OvertimeStatus.APPROVED
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = request
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(employee_id, request_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INVALID_STATUS_TRANSITION"

    async def test_rejects_cancel_for_rejected_request(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should return 409 INVALID_STATUS_TRANSITION for rejected requests."""
        request_id = uuid4()
        request = _make_overtime_request(
            employee_id, request_id=request_id, status=OvertimeStatus.REJECTED
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = request
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(employee_id, request_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INVALID_STATUS_TRANSITION"

    async def test_returns_404_for_nonexistent_request(
        self, service: ESSOvertimeService, mock_session: AsyncMock, employee_id: UUID
    ) -> None:
        """Should return 404 when the request doesn't exist."""
        request_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(employee_id, request_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "OVERTIME_REQUEST_NOT_FOUND"
