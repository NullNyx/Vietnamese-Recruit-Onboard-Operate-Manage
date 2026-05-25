"""ESS-specific FastAPI dependencies.

Provides the `get_current_employee` dependency that extracts and validates
the employee_id from the JWT token, enforcing that all ESS endpoints
require a valid token with an employee_id claim.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Request

from src.modules.identity.application.token_service import TokenService
from src.modules.identity.container import get_token_service
from src.modules.identity.domain.exceptions import InvalidTokenError


async def get_current_employee(
    request: Request,
    token_service: TokenService = Depends(get_token_service),
) -> UUID:
    """Extract and validate employee_id from JWT token in access_token cookie.

    Reads the JWT from the ``access_token`` cookie, verifies it via
    TokenService, and extracts the ``employee_id`` claim. This is the
    single enforcement point for ESS authentication and employee linking.

    Args:
        request: The incoming FastAPI request object.
        token_service: Service for JWT token verification (injected).

    Returns:
        The authenticated employee's UUID.

    Raises:
        HTTPException: 401 if no token or token is invalid/expired.
        HTTPException: 403 with NO_EMPLOYEE_LINK code if the token
            does not contain an employee_id claim.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        payload = token_service.verify_access_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not payload.employee_id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "NO_EMPLOYEE_LINK",
                "message": "No employee profile linked to this account",
            },
        )

    return payload.employee_id
