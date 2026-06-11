"""Integration tests for leave request API endpoints.

Tests HTTP status codes, response shapes, and error handling through
the FastAPI router using mocked dependencies.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.modules.employee.api.dependencies import get_current_employee
from src.modules.employee.domain.entities import Employee
from src.modules.employee_request.api.router import employee_request_router
from src.modules.employee_request.application.leave_service import LeaveService
from src.modules.employee_request.container import get_leave_service


@pytest.fixture
def app():
    """Create a test app with the employee request router."""
    app = FastAPI()
    app.include_router(employee_request_router)
    return app


@pytest.fixture
def mock_employee():
    """Return a mock active employee."""
    emp = MagicMock(spec=Employee)
    emp.id = uuid4()
    emp.is_active = True
    return emp


@pytest.fixture
def mock_leave_service():
    """Return a mock LeaveService."""
    return AsyncMock(spec=LeaveService)


class TestCreateLeaveAPI:
    """Tests for POST /api/employee-requests/me/leave."""

    @pytest.mark.asyncio
    async def test_returns_201_on_success(self, app, mock_employee, mock_leave_service):
        """Returns 201 with success message and request data."""
        app.dependency_overrides[get_current_employee] = lambda: mock_employee
        app.dependency_overrides[get_leave_service] = lambda: mock_leave_service

        from src.modules.employee_request.domain.entities import EmployeeRequest
        from src.modules.employee_request.domain.enums import LeaveType, RequestStatus

        created = MagicMock(spec=EmployeeRequest)
        created.id = uuid4()
        created.employee_id = mock_employee.id
        created.request_type = "leave"
        created.status = RequestStatus.SUBMITTED
        created.leave_type = LeaveType.ANNUAL
        created.start_date = date(2026, 6, 15)
        created.end_date = date(2026, 6, 17)
        created.reason = "Vacation"
        created.submitted_at = None
        created.updated_at = None
        created.cancellation_reason = None

        mock_leave_service.create_leave = AsyncMock(return_value=created)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/employee-requests/me/leave",
                json={
                    "leave_type": "annual",
                    "start_date": "2026-06-15",
                    "end_date": "2026-06-17",
                    "reason": "Vacation",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Leave request submitted"
        assert data["request"]["status"] == "submitted"
        assert data["request"]["leave_type"] == "annual"
        assert data["request"]["start_date"] == "2026-06-15"
        assert data["request"]["end_date"] == "2026-06-17"
        assert data["request"]["reason"] == "Vacation"

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_leave_type(self, app, mock_employee, mock_leave_service):
        """Invalid leave_type returns 422."""
        app.dependency_overrides[get_current_employee] = lambda: mock_employee
        app.dependency_overrides[get_leave_service] = lambda: mock_leave_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/employee-requests/me/leave",
                json={
                    "leave_type": "maternity",
                    "start_date": "2026-06-15",
                    "end_date": "2026-06-17",
                    "reason": "Maternity",
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_for_end_before_start(self, app, mock_employee, mock_leave_service):
        """end_date before start_date returns 422."""
        app.dependency_overrides[get_current_employee] = lambda: mock_employee
        app.dependency_overrides[get_leave_service] = lambda: mock_leave_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/employee-requests/me/leave",
                json={
                    "leave_type": "annual",
                    "start_date": "2026-06-17",
                    "end_date": "2026-06-15",
                    "reason": "Invalid",
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_authenticated_employee(self, app, mock_leave_service):
        """Returns 403 when no authenticated employee."""
        app.dependency_overrides[get_current_employee] = lambda: None
        app.dependency_overrides[get_leave_service] = lambda: mock_leave_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/employee-requests/me/leave",
                json={
                    "leave_type": "annual",
                    "start_date": "2026-06-15",
                    "end_date": "2026-06-17",
                    "reason": "Vacation",
                },
            )

        assert response.status_code == 403
        assert "Only employees" in response.json()["detail"]


class TestCancelLeaveAPI:
    """Tests for POST /api/employee-requests/me/leave/{id}/cancel."""

    @pytest.mark.asyncio
    async def test_returns_200_on_success(self, app, mock_employee, mock_leave_service):
        """Returns 200 with success message."""
        app.dependency_overrides[get_current_employee] = lambda: mock_employee
        app.dependency_overrides[get_leave_service] = lambda: mock_leave_service

        from src.modules.employee_request.domain.entities import EmployeeRequest
        from src.modules.employee_request.domain.enums import RequestStatus

        cancelled = MagicMock(spec=EmployeeRequest)
        cancelled.id = uuid4()
        cancelled.employee_id = mock_employee.id
        cancelled.status = RequestStatus.CANCELLED
        cancelled.cancellation_reason = "Changed mind"
        cancelled.leave_type = None
        cancelled.start_date = None
        cancelled.end_date = None
        cancelled.reason = None
        cancelled.submitted_at = None
        cancelled.updated_at = None

        mock_leave_service.cancel_leave = AsyncMock(return_value=cancelled)

        request_id = uuid4()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/employee-requests/me/leave/{request_id}/cancel",
                json={"cancellation_reason": "Changed mind"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Leave request cancelled"
        assert data["request"]["status"] == "cancelled"


class TestListLeaveAPI:
    """Tests for GET /api/employee-requests/me/leave."""

    @pytest.mark.asyncio
    async def test_returns_200_with_requests(self, app, mock_employee, mock_leave_service):
        """Returns 200 with list of leave requests."""
        app.dependency_overrides[get_current_employee] = lambda: mock_employee
        app.dependency_overrides[get_leave_service] = lambda: mock_leave_service

        mock_leave_service.list_my_leaves = AsyncMock(return_value=[])

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/employee-requests/me/leave")

        assert response.status_code == 200
        data = response.json()
        assert data["requests"] == []
