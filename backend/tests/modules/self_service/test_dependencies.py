"""Unit tests for ESS dependencies (get_current_employee).

Tests the FastAPI dependency that extracts and validates the employee_id
from the access_token cookie for self-service endpoints.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.identity.api.schemas import TokenPayload
from src.modules.identity.domain.exceptions import InvalidTokenError
from src.modules.self_service.api.dependencies import get_current_employee


@pytest.fixture
def employee_id():
    """Generate a fixed employee UUID for tests."""
    return uuid4()


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request with a valid access_token cookie."""
    request = MagicMock()
    request.cookies = {"access_token": "valid-jwt-token"}
    return request


@pytest.fixture
def mock_token_service(employee_id):
    """Create a mock TokenService that returns a payload with employee_id."""
    service = MagicMock()
    service.verify_access_token.return_value = TokenPayload(
        sub=uuid4(),
        email="employee@example.com",
        employee_id=employee_id,
        exp=1700000000,
        iat=1699999000,
    )
    return service


@pytest.fixture
def mock_token_service_no_employee():
    """Create a mock TokenService that returns a payload without employee_id."""
    service = MagicMock()
    service.verify_access_token.return_value = TokenPayload(
        sub=uuid4(),
        email="user@example.com",
        employee_id=None,
        exp=1700000000,
        iat=1699999000,
    )
    return service


class TestGetCurrentEmployee:
    """Tests for the get_current_employee dependency."""

    async def test_returns_employee_id_on_valid_token(
        self, mock_request, mock_token_service, employee_id
    ):
        """Should return the employee_id UUID when token is valid and has employee_id."""
        result = await get_current_employee(mock_request, mock_token_service)

        assert result == employee_id

    async def test_extracts_token_from_cookie(
        self, mock_request, mock_token_service
    ):
        """Should read the access_token from request cookies."""
        await get_current_employee(mock_request, mock_token_service)

        mock_token_service.verify_access_token.assert_called_once_with(
            "valid-jwt-token"
        )

    async def test_raises_401_when_cookie_missing(self, mock_token_service):
        """Should raise HTTPException 401 when access_token cookie is absent."""
        request = MagicMock()
        request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_employee(request, mock_token_service)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"

    async def test_raises_401_when_cookie_is_none(self, mock_token_service):
        """Should raise HTTPException 401 when access_token cookie returns None."""
        request = MagicMock()
        request.cookies = {"access_token": None}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_employee(request, mock_token_service)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"

    async def test_raises_401_when_token_invalid(
        self, mock_request, mock_token_service
    ):
        """Should raise HTTPException 401 when token verification fails."""
        mock_token_service.verify_access_token.side_effect = InvalidTokenError()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_employee(mock_request, mock_token_service)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired token"

    async def test_raises_403_when_no_employee_id(
        self, mock_request, mock_token_service_no_employee
    ):
        """Should raise HTTPException 403 with NO_EMPLOYEE_LINK when no employee_id in token."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_employee(mock_request, mock_token_service_no_employee)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "NO_EMPLOYEE_LINK"
        assert "employee profile" in exc_info.value.detail["message"].lower()

    async def test_raises_401_when_cookie_empty_string(self, mock_token_service):
        """Should raise HTTPException 401 when access_token cookie is empty string."""
        request = MagicMock()
        request.cookies = {"access_token": ""}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_employee(request, mock_token_service)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"
