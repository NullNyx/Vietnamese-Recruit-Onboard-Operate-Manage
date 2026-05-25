"""Unit tests for ESSLeaveService."""

from datetime import date, timedelta, datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.attendance.domain.entities import LeaveBalance, LeaveRequest, LeaveType
from src.modules.self_service.api.schemas import ESSLeaveRequestCreate
from src.modules.self_service.application.ess_leave_service import ESSLeaveService


@pytest.fixture
def balance_repo() -> AsyncMock:
    """Create a mock LeaveBalanceRepository."""
    return AsyncMock()


@pytest.fixture
def request_repo() -> AsyncMock:
    """Create a mock LeaveRequestRepository."""
    return AsyncMock()


@pytest.fixture
def type_repo() -> AsyncMock:
    """Create a mock LeaveTypeRepository."""
    return AsyncMock()


@pytest.fixture
def session() -> AsyncMock:
    """Create a mock AsyncSession."""
    return AsyncMock()


@pytest.fixture
def service(
    balance_repo: AsyncMock,
    request_repo: AsyncMock,
    type_repo: AsyncMock,
    session: AsyncMock,
) -> ESSLeaveService:
    """Create an ESSLeaveService with mocked dependencies."""
    return ESSLeaveService(
        balance_repo=balance_repo,
        request_repo=request_repo,
        type_repo=type_repo,
        session=session,
    )


def _make_leave_type(**overrides) -> LeaveType:
    """Create a test LeaveType entity."""
    defaults = {
        "id": uuid4(),
        "name": "annual",
        "display_name": "Annual Leave",
        "default_days_per_year": 12,
        "is_paid": True,
        "requires_approval": True,
        "requires_document": False,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return LeaveType(**defaults)


def _make_leave_balance(**overrides) -> LeaveBalance:
    """Create a test LeaveBalance entity."""
    defaults = {
        "id": uuid4(),
        "employee_id": uuid4(),
        "leave_type_id": uuid4(),
        "year": date.today().year,
        "total_days": Decimal("12.0"),
        "used_days": Decimal("3.0"),
        "remaining_days": Decimal("9.0"),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return LeaveBalance(**defaults)


def _make_leave_request(**overrides) -> LeaveRequest:
    """Create a test LeaveRequest entity."""
    defaults = {
        "id": uuid4(),
        "employee_id": uuid4(),
        "leave_type_id": uuid4(),
        "start_date": date.today() + timedelta(days=5),
        "end_date": date.today() + timedelta(days=7),
        "total_days": Decimal("3.0"),
        "reason": "Family vacation",
        "status": "pending",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return LeaveRequest(**defaults)


class TestGetBalances:
    """Tests for ESSLeaveService.get_balances."""

    async def test_returns_balances_for_current_year(
        self,
        service: ESSLeaveService,
        balance_repo: AsyncMock,
        type_repo: AsyncMock,
    ) -> None:
        """get_balances returns all leave type balances for the current year."""
        emp_id = uuid4()
        lt_id = uuid4()
        leave_type = _make_leave_type(id=lt_id, display_name="Annual Leave")
        balance = _make_leave_balance(
            employee_id=emp_id,
            leave_type_id=lt_id,
            total_days=Decimal("12.0"),
            used_days=Decimal("3.0"),
            remaining_days=Decimal("9.0"),
        )

        balance_repo.get_by_employee_year.return_value = [balance]
        type_repo.list_all.return_value = [leave_type]

        result = await service.get_balances(emp_id)

        assert len(result) == 1
        assert result[0].leave_type_id == lt_id
        assert result[0].leave_type_name == "Annual Leave"
        assert result[0].total_days == Decimal("12.0")
        assert result[0].used_days == Decimal("3.0")
        assert result[0].remaining_days == Decimal("9.0")

        balance_repo.get_by_employee_year.assert_called_once_with(
            emp_id, date.today().year
        )

    async def test_returns_empty_list_when_no_balances(
        self,
        service: ESSLeaveService,
        balance_repo: AsyncMock,
        type_repo: AsyncMock,
    ) -> None:
        """get_balances returns empty list when no balances exist."""
        balance_repo.get_by_employee_year.return_value = []
        type_repo.list_all.return_value = []

        result = await service.get_balances(uuid4())

        assert result == []

    async def test_returns_multiple_leave_types(
        self,
        service: ESSLeaveService,
        balance_repo: AsyncMock,
        type_repo: AsyncMock,
    ) -> None:
        """get_balances returns balances for multiple leave types."""
        emp_id = uuid4()
        lt1_id = uuid4()
        lt2_id = uuid4()

        leave_types = [
            _make_leave_type(id=lt1_id, name="annual", display_name="Annual Leave"),
            _make_leave_type(id=lt2_id, name="sick", display_name="Sick Leave"),
        ]
        balances = [
            _make_leave_balance(employee_id=emp_id, leave_type_id=lt1_id),
            _make_leave_balance(employee_id=emp_id, leave_type_id=lt2_id),
        ]

        balance_repo.get_by_employee_year.return_value = balances
        type_repo.list_all.return_value = leave_types

        result = await service.get_balances(emp_id)

        assert len(result) == 2


class TestGetRequests:
    """Tests for ESSLeaveService.get_requests."""

    async def test_returns_all_requests_for_employee(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
        type_repo: AsyncMock,
    ) -> None:
        """get_requests returns all leave requests for the employee."""
        emp_id = uuid4()
        lt_id = uuid4()
        leave_type = _make_leave_type(id=lt_id, display_name="Annual Leave")
        req = _make_leave_request(employee_id=emp_id, leave_type_id=lt_id)

        request_repo.list_by_employee.return_value = ([req], 1)
        type_repo.list_all.return_value = [leave_type]

        result = await service.get_requests(emp_id)

        assert len(result) == 1
        assert result[0].id == req.id
        assert result[0].leave_type_name == "Annual Leave"
        assert result[0].status == "pending"

    async def test_returns_empty_list_when_no_requests(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
        type_repo: AsyncMock,
    ) -> None:
        """get_requests returns empty list when no requests exist."""
        request_repo.list_by_employee.return_value = ([], 0)
        type_repo.list_all.return_value = []

        result = await service.get_requests(uuid4())

        assert result == []


class TestCreateRequest:
    """Tests for ESSLeaveService.create_request."""

    async def test_creates_request_with_valid_data(
        self,
        service: ESSLeaveService,
        balance_repo: AsyncMock,
        request_repo: AsyncMock,
        type_repo: AsyncMock,
        session: AsyncMock,
    ) -> None:
        """create_request creates a leave request with status 'pending'."""
        emp_id = uuid4()
        lt_id = uuid4()
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=7)

        balance = _make_leave_balance(
            employee_id=emp_id,
            leave_type_id=lt_id,
            remaining_days=Decimal("9.0"),
        )
        leave_type = _make_leave_type(id=lt_id, display_name="Annual Leave")

        balance_repo.get_balance.return_value = balance
        type_repo.get_by_id.return_value = leave_type

        created_request = _make_leave_request(
            employee_id=emp_id,
            leave_type_id=lt_id,
            start_date=start,
            end_date=end,
            total_days=Decimal("3.0"),
            status="pending",
        )
        request_repo.create.return_value = created_request

        data = ESSLeaveRequestCreate(
            leave_type_id=lt_id,
            start_date=start,
            end_date=end,
            reason="Vacation",
        )

        result = await service.create_request(emp_id, data)

        assert result.status == "pending"
        assert result.leave_type_name == "Annual Leave"
        request_repo.create.assert_called_once()
        session.commit.assert_called_once()

    async def test_rejects_past_start_date(
        self,
        service: ESSLeaveService,
    ) -> None:
        """create_request raises 422 INVALID_DATE_RANGE for past start_date."""
        emp_id = uuid4()
        data = ESSLeaveRequestCreate(
            leave_type_id=uuid4(),
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=2),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(emp_id, data)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_DATE_RANGE"

    async def test_rejects_end_date_before_start_date(
        self,
        service: ESSLeaveService,
    ) -> None:
        """create_request raises 422 INVALID_DATE_RANGE when end < start."""
        emp_id = uuid4()
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=3)

        data = ESSLeaveRequestCreate(
            leave_type_id=uuid4(),
            start_date=start,
            end_date=end,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(emp_id, data)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_DATE_RANGE"

    async def test_rejects_insufficient_balance(
        self,
        service: ESSLeaveService,
        balance_repo: AsyncMock,
    ) -> None:
        """create_request raises 422 INSUFFICIENT_LEAVE_BALANCE when balance too low."""
        emp_id = uuid4()
        lt_id = uuid4()
        start = date.today() + timedelta(days=1)
        end = date.today() + timedelta(days=10)  # 10 days requested

        balance = _make_leave_balance(
            employee_id=emp_id,
            leave_type_id=lt_id,
            remaining_days=Decimal("5.0"),  # Only 5 remaining
        )
        balance_repo.get_balance.return_value = balance

        data = ESSLeaveRequestCreate(
            leave_type_id=lt_id,
            start_date=start,
            end_date=end,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(emp_id, data)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INSUFFICIENT_LEAVE_BALANCE"

    async def test_rejects_when_no_balance_record(
        self,
        service: ESSLeaveService,
        balance_repo: AsyncMock,
    ) -> None:
        """create_request raises 422 when no balance record exists."""
        emp_id = uuid4()
        start = date.today() + timedelta(days=1)
        end = date.today() + timedelta(days=3)

        balance_repo.get_balance.return_value = None

        data = ESSLeaveRequestCreate(
            leave_type_id=uuid4(),
            start_date=start,
            end_date=end,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(emp_id, data)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INSUFFICIENT_LEAVE_BALANCE"

    async def test_calculates_total_days_correctly(
        self,
        service: ESSLeaveService,
        balance_repo: AsyncMock,
        request_repo: AsyncMock,
        type_repo: AsyncMock,
        session: AsyncMock,
    ) -> None:
        """create_request calculates total_days as (end - start).days + 1."""
        emp_id = uuid4()
        lt_id = uuid4()
        start = date.today() + timedelta(days=1)
        end = date.today() + timedelta(days=3)  # 3 days total

        balance = _make_leave_balance(
            employee_id=emp_id,
            leave_type_id=lt_id,
            remaining_days=Decimal("10.0"),
        )
        leave_type = _make_leave_type(id=lt_id)

        balance_repo.get_balance.return_value = balance
        type_repo.get_by_id.return_value = leave_type

        created_request = _make_leave_request(
            employee_id=emp_id,
            leave_type_id=lt_id,
            start_date=start,
            end_date=end,
            total_days=Decimal("3.0"),
        )
        request_repo.create.return_value = created_request

        data = ESSLeaveRequestCreate(
            leave_type_id=lt_id,
            start_date=start,
            end_date=end,
        )

        await service.create_request(emp_id, data)

        # Verify the LeaveRequest passed to create has correct total_days
        call_args = request_repo.create.call_args[0][0]
        assert call_args.total_days == Decimal("3")


class TestCancelRequest:
    """Tests for ESSLeaveService.cancel_request."""

    async def test_cancels_pending_request(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
        type_repo: AsyncMock,
        session: AsyncMock,
    ) -> None:
        """cancel_request updates status to 'cancelled' for pending requests."""
        emp_id = uuid4()
        req_id = uuid4()
        lt_id = uuid4()

        leave_request = _make_leave_request(
            id=req_id,
            employee_id=emp_id,
            leave_type_id=lt_id,
            status="pending",
        )
        leave_type = _make_leave_type(id=lt_id, display_name="Annual Leave")

        request_repo.get_by_id.return_value = leave_request
        request_repo.update.return_value = leave_request
        type_repo.get_by_id.return_value = leave_type

        result = await service.cancel_request(emp_id, req_id)

        assert result.status == "cancelled"
        session.commit.assert_called_once()

    async def test_rejects_when_not_owned(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
    ) -> None:
        """cancel_request raises 403 RESOURCE_FORBIDDEN when request belongs to another employee."""
        emp_id = uuid4()
        other_emp_id = uuid4()
        req_id = uuid4()

        leave_request = _make_leave_request(
            id=req_id,
            employee_id=other_emp_id,
            status="pending",
        )
        request_repo.get_by_id.return_value = leave_request

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(emp_id, req_id)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "RESOURCE_FORBIDDEN"

    async def test_rejects_non_pending_status(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
    ) -> None:
        """cancel_request raises 409 INVALID_STATUS_TRANSITION for non-pending requests."""
        emp_id = uuid4()
        req_id = uuid4()

        leave_request = _make_leave_request(
            id=req_id,
            employee_id=emp_id,
            status="approved",
        )
        request_repo.get_by_id.return_value = leave_request

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(emp_id, req_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INVALID_STATUS_TRANSITION"

    async def test_rejects_cancelled_status(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
    ) -> None:
        """cancel_request raises 409 for already cancelled requests."""
        emp_id = uuid4()
        req_id = uuid4()

        leave_request = _make_leave_request(
            id=req_id,
            employee_id=emp_id,
            status="cancelled",
        )
        request_repo.get_by_id.return_value = leave_request

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(emp_id, req_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INVALID_STATUS_TRANSITION"

    async def test_rejects_rejected_status(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
    ) -> None:
        """cancel_request raises 409 for rejected requests."""
        emp_id = uuid4()
        req_id = uuid4()

        leave_request = _make_leave_request(
            id=req_id,
            employee_id=emp_id,
            status="rejected",
        )
        request_repo.get_by_id.return_value = leave_request

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(emp_id, req_id)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INVALID_STATUS_TRANSITION"

    async def test_raises_404_when_request_not_found(
        self,
        service: ESSLeaveService,
        request_repo: AsyncMock,
    ) -> None:
        """cancel_request raises 404 when request doesn't exist."""
        request_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_request(uuid4(), uuid4())

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "LEAVE_REQUEST_NOT_FOUND"
