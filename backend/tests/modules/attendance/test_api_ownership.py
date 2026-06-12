"""API-layer tests for check-in/check-out ownership and access control.

Tests the FastAPI router endpoints using mocked dependencies (no database).
Covers:

- Missing Employee link → 403.
- Inactive Employee → 403.
- X-Forwarded-For from untrusted client not trusted.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from src.modules.attendance.api.error_handler import register_attendance_error_handlers
from src.modules.attendance.api.router import (
    attendance_router,
    get_client_ip,
)
from src.modules.attendance.container import get_attendance_service
from src.modules.attendance.domain.entities import AttendanceRecord, AttendanceSource
from src.modules.employee.api.dependencies import get_current_employee
from src.modules.identity.api.error_handler import register_auth_error_handlers

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeEmployee:
    """Minimal employee stub for dependency override."""

    def __init__(self, employee_id: str = "employee-uuid", is_active: bool = True):
        self.id = employee_id
        self.is_active = is_active
        self.user_id = "user-uuid"
        self.email = "employee@example.com"


class FakeAttendanceService:
    """Stand-in for AttendanceService."""

    def __init__(self) -> None:
        self.check_in_result = AttendanceRecord(
            id=uuid4(),
            employee_id=uuid4(),
            work_date=date.today(),
            check_in_at=datetime.now(UTC),
            check_in_ip="192.168.1.100",
            source=AttendanceSource.WEB,
        )

    async def check_in(self, employee_id, client_ip, user_agent=None):
        return self.check_in_result

    async def check_out(self, employee_id, client_ip, user_agent=None):
        return self.check_in_result

    async def get_history(self, employee_id, year=None, month=None, days=7):
        return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_get_current_employee(employee: FakeEmployee | None):
    """Return a fake dependency that mirrors real get_current_employee logic.

    Raises 403 when:
    - employee is None (no linked record for non-admin)
    - employee.is_active is False
    """

    async def _dep():
        if employee is None:
            raise HTTPException(status_code=403, detail="Employee record not found")
        if not employee.is_active:
            raise HTTPException(status_code=403, detail="Employee account is inactive")
        return employee

    return _dep


def _build_app(
    employee: FakeEmployee | None = None,
    service: FakeAttendanceService | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(attendance_router)
    register_attendance_error_handlers(app)
    register_auth_error_handlers(app)
    app.dependency_overrides[get_current_employee] = _make_get_current_employee(employee)
    app.dependency_overrides[get_attendance_service] = lambda: service or FakeAttendanceService()
    return app


# ---------------------------------------------------------------------------
# Ownership / Access-control tests
# ---------------------------------------------------------------------------


class TestCheckInOwnership:
    """Check-in requires active Employee linked to current user."""

    def test_missing_employee_link_returns_403(self) -> None:
        """No Employee record → 403."""
        app = _build_app(employee=None)
        client = TestClient(app)
        resp = client.post("/api/attendance/me/check-in")
        assert resp.status_code == 403

    def test_inactive_employee_returns_403(self) -> None:
        """Inactive Employee → 403."""
        app = _build_app(employee=FakeEmployee(is_active=False))
        client = TestClient(app)
        resp = client.post("/api/attendance/me/check-in")
        assert resp.status_code == 403


class TestCheckOutOwnership:
    """Check-out requires active Employee linked to current user."""

    def test_missing_employee_link_returns_403(self) -> None:
        """No Employee record → 403."""
        app = _build_app(employee=None)
        client = TestClient(app)
        resp = client.post("/api/attendance/me/check-out")
        assert resp.status_code == 403

    def test_inactive_employee_returns_403(self) -> None:
        """Inactive Employee → 403."""
        app = _build_app(employee=FakeEmployee(is_active=False))
        client = TestClient(app)
        resp = client.post("/api/attendance/me/check-out")
        assert resp.status_code == 403


class TestHistoryPartialParams:
    """History endpoint rejects partial year/month params."""

    def test_only_year_returns_422(self) -> None:
        """Passing year without month -> 422."""
        app = _build_app(employee=FakeEmployee())
        client = TestClient(app)
        resp = client.get("/api/attendance/me/history?year=2026")
        assert resp.status_code == 422

    def test_only_month_returns_422(self) -> None:
        """Passing month without year -> 422."""
        app = _build_app(employee=FakeEmployee())
        client = TestClient(app)
        resp = client.get("/api/attendance/me/history?month=6")
        assert resp.status_code == 422

    def test_both_year_and_month_returns_200(self) -> None:
        """Passing both year and month -> 200."""
        app = _build_app(employee=FakeEmployee())
        client = TestClient(app)
        resp = client.get("/api/attendance/me/history?year=2026&month=6")
        assert resp.status_code == 200

    def test_only_days_returns_200(self) -> None:
        """Passing only days -> 200."""
        app = _build_app(employee=FakeEmployee())
        client = TestClient(app)
        resp = client.get("/api/attendance/me/history?days=7")
        assert resp.status_code == 200


class TestClientIpExtraction:
    """X-Forwarded-For from untrusted client is ignored."""

    def test_trusted_proxy_ip_used(self) -> None:
        """When client is 127.0.0.1, X-Forwarded-For is trusted."""
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = Headers({"X-Forwarded-For": "203.0.113.50"})

        result = asyncio.run(get_client_ip(mock_request))
        assert result == "203.0.113.50"

    def test_untrusted_proxy_ip_ignored(self) -> None:
        """When client is not trusted, X-Forwarded-For is ignored."""
        mock_request = MagicMock()
        mock_request.client.host = "203.0.113.50"
        mock_request.headers = Headers({"X-Forwarded-For": "10.0.0.1"})

        result = asyncio.run(get_client_ip(mock_request))
        assert result == "203.0.113.50"

    def test_direct_connection_client_ip_used(self) -> None:
        """Direct connection returns client IP."""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = Headers({})

        result = asyncio.run(get_client_ip(mock_request))
        assert result == "192.168.1.100"

    def test_no_client_returns_localhost(self) -> None:
        """When no client info, default to localhost."""
        mock_request = MagicMock()
        mock_request.client = None
        mock_request.headers = Headers({})

        result = asyncio.run(get_client_ip(mock_request))
        assert result == "127.0.0.1"
