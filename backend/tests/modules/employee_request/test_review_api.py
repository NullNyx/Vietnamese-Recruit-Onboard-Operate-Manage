"""Integration tests for HR review API endpoints.

Tests the admin review queue, approve, and reject endpoints with
mocked dependencies following the project's test patterns.
"""

from __future__ import annotations

import os

os.environ["AUTH_GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["AUTH_GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["AUTH_JWT_SECRET_KEY"] = "test-secret-key-32-chars-min-for-hs256!"
os.environ["AUTH_OAUTH_TOKEN_ENCRYPTION_KEY"] = "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw=="

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.employee_request.api.admin_router import (
    AdminEmployeeRequestItem,
    admin_employee_request_router,
)
from src.modules.employee_request.api.error_handler import (
    register_employee_request_error_handlers,
)
from src.modules.employee_request.container import (
    get_employee_request_repository,
    get_employee_request_review_service,
)
from src.modules.employee_request.domain.exceptions import (
    RequestNotFoundError,
    RequestNotReviewableError,
)
from src.modules.employee_request.infrastructure.employee_request_repository import (
    SubmittedRequestWithEmployee,
)
from src.modules.identity.domain.entities import User, UserRole


def _make_admin() -> User:
    return User(
        id=uuid4(),
        email="admin@example.com",
        name="Admin User",
        avatar_url=None,
        google_sub=f"google-sub-{uuid4().hex[:8]}",
        created_at=datetime.now(UTC),
        last_login=datetime.now(UTC),
        is_active=True,
        role=UserRole.ADMIN,
    )


def _build_app(
    admin_user: User | None = None,
    mock_repo: AsyncMock | None = None,
    mock_review_service: AsyncMock | None = None,
) -> FastAPI:
    """Create a test app with optional overrides."""
    app = FastAPI()
    app.include_router(admin_employee_request_router)
    register_employee_request_error_handlers(app)

    if admin_user is not None:
        # Override get_current_user so require_admin still runs its role check
        from src.modules.identity.container import get_current_user

        async def _override_current_user() -> User:
            return admin_user
        app.dependency_overrides[get_current_user] = _override_current_user

    if mock_repo is not None:
        async def _override_repo() -> AsyncMock:
            return mock_repo
        app.dependency_overrides[get_employee_request_repository] = _override_repo

    if mock_review_service is not None:
        async def _override_service() -> AsyncMock:
            return mock_review_service
        app.dependency_overrides[get_employee_request_review_service] = _override_service

    return app


def _model_dump_kwargs(
    request_id,
    employee_id,
    status="submitted",
    request_type="leave",
) -> dict:
    """Simulates EmployeeRequest.model_dump() — no employee_name field."""
    return {
        "id": str(request_id),
        "employee_id": str(employee_id),
        "request_type": request_type,
        "status": status,
        "submitted_at": None,
        "updated_at": None,
        "reason": None,
        "work_date": None,
        "start_time": None,
        "end_time": None,
        "duration_minutes": None,
        "leave_type": None,
        "start_date": None,
        "end_date": None,
        "cancellation_reason": None,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestListReviewQueue:
    """Tests for GET /api/admin/employee-requests."""

    def test_returns_200_with_submitted_requests(self) -> None:
        """Returns 200 with list of submitted requests."""
        admin = _make_admin()
        mock_repo = AsyncMock()

        req_id = uuid4()
        emp_id = uuid4()
        mock_request = MagicMock()
        mock_request.model_dump.return_value = _model_dump_kwargs(
            req_id, emp_id, status="submitted",
        )

        mock_repo.get_all_submitted = AsyncMock(
            return_value=[
                SubmittedRequestWithEmployee(
                    request=mock_request,
                    employee_name="Nguyen Van A",
                ),
            ],
        )

        app = _build_app(admin_user=admin, mock_repo=mock_repo)
        client = TestClient(app)
        response = client.get("/api/admin/employee-requests")

        assert response.status_code == 200
        data = response.json()
        assert len(data["requests"]) == 1
        assert data["requests"][0]["id"] == str(req_id)
        assert data["requests"][0]["employee_name"] == "Nguyen Van A"
        assert data["requests"][0]["request_type"] == "leave"
        assert data["requests"][0]["status"] == "submitted"


class TestApproveRequest:
    """Tests for POST /api/admin/employee-requests/{id}/approve."""

    def test_returns_200_on_success(self) -> None:
        """Returns 200 when approve succeeds."""
        admin = _make_admin()
        mock_service = AsyncMock()

        request_id = uuid4()
        emp_id = uuid4()
        item = AdminEmployeeRequestItem(
            **_model_dump_kwargs(request_id, emp_id, status="approved"),
            employee_name="Nguyen Van A",
        )
        mock_service.approve_request = AsyncMock(return_value=item)

        app = _build_app(admin_user=admin, mock_review_service=mock_service)
        client = TestClient(app)
        response = client.post(
            f"/api/admin/employee-requests/{request_id}/approve",
            json={"review_reason": "Approved by HR"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Request approved"
        assert data["request"]["status"] == "approved"
        assert data["request"]["id"] == str(request_id)

    def test_returns_400_when_not_submitted(self) -> None:
        """Returns 400 when request is not in SUBMITTED state."""
        admin = _make_admin()
        mock_service = AsyncMock()

        request_id = uuid4()
        mock_service.approve_request = AsyncMock(
            side_effect=RequestNotReviewableError(
                request_id=request_id,
                current_status="approved",
            ),
        )

        app = _build_app(admin_user=admin, mock_review_service=mock_service)
        client = TestClient(app)
        response = client.post(
            f"/api/admin/employee-requests/{request_id}/approve",
            json={"review_reason": None},
        )

        assert response.status_code == 400
        data = response.json()
        assert "only submitted" in data["detail"].lower()

    def test_returns_404_when_not_found(self) -> None:
        """Returns 404 when request does not exist."""
        admin = _make_admin()
        mock_service = AsyncMock()

        request_id = uuid4()
        mock_service.approve_request = AsyncMock(
            side_effect=RequestNotFoundError(request_id),
        )

        app = _build_app(admin_user=admin, mock_review_service=mock_service)
        client = TestClient(app)
        response = client.post(
            f"/api/admin/employee-requests/{request_id}/approve",
            json={},
        )

        assert response.status_code == 404
        data = response.json()
        assert str(request_id) in data["detail"]


class TestRejectRequest:
    """Tests for POST /api/admin/employee-requests/{id}/reject."""

    def test_returns_200_on_success(self) -> None:
        """Returns 200 when reject succeeds."""
        admin = _make_admin()
        mock_service = AsyncMock()

        request_id = uuid4()
        emp_id = uuid4()
        item = AdminEmployeeRequestItem(
            **_model_dump_kwargs(request_id, emp_id, status="rejected"),
            employee_name="Nguyen Van A",
        )
        mock_service.reject_request = AsyncMock(return_value=item)

        app = _build_app(admin_user=admin, mock_review_service=mock_service)
        client = TestClient(app)
        response = client.post(
            f"/api/admin/employee-requests/{request_id}/reject",
            json={"review_reason": "Budget constraints"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Request rejected"
        assert data["request"]["status"] == "rejected"
        assert data["request"]["id"] == str(request_id)

    def test_returns_403_when_not_admin(self) -> None:
        """Returns 403 when authenticated user is not admin."""
        non_admin = User(
            id=uuid4(),
            email="user@example.com",
            name="Regular User",
            avatar_url=None,
            google_sub=f"google-sub-{uuid4().hex[:8]}",
            created_at=datetime.now(UTC),
            last_login=datetime.now(UTC),
            is_active=True,
            role=UserRole.USER,
        )
        app = _build_app(admin_user=non_admin)
        client = TestClient(app)
        response = client.post(
            f"/api/admin/employee-requests/{uuid4()}/reject",
            json={},
        )

        assert response.status_code == 403
