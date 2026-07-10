"""FastAPI router for the Identity & Auth module.

Defines the /api/auth/* endpoints for first-run setup, local login,
password change, token refresh, logout, and user profile retrieval.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from src.database import get_session
from src.modules.employee.domain.entities import Employee
from src.modules.identity.api.schemas import (
    AuthLoginRequest,
    AuthSessionResponse,
    ChangePasswordRequest,
    FirstRunSetupRequest,
    GrantStatusResponse,
    SetupStatusResponse,
    UserResponse,
)
from src.modules.identity.application.auth_service import AuthService
from src.modules.identity.application.oauth_service import OAuthService
from src.modules.identity.application.token_service import TokenService
from src.modules.identity.container import (
    get_auth_service,
    get_current_user,
    get_oauth_service,
    get_rate_limiter,
    get_token_service,
)
from src.modules.identity.domain.entities import User
from src.modules.identity.domain.exceptions import (
    InvalidTokenError,
    RateLimitExceededError,
)
from src.modules.identity.infrastructure.rate_limiter import RateLimiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Cookie configuration constants.
_ACCESS_TOKEN_MAX_AGE = 15 * 60  # 15 minutes
_REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60  # 7 days
_PASSWORD_CHANGE_MAX_AGE = _ACCESS_TOKEN_MAX_AGE


# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
OAuthServiceDep = Annotated[OAuthService, Depends(get_oauth_service)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def _set_session_cookies(
    response: JSONResponse,
    *,
    access_token: str,
    refresh_token: str,
    must_change_password: bool,
) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=_ACCESS_TOKEN_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=_REFRESH_TOKEN_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    if must_change_password:
        response.set_cookie(
            key="must_change_password",
            value="true",
            max_age=_PASSWORD_CHANGE_MAX_AGE,
            httponly=True,
            secure=True,
            samesite="lax",
        )
    else:
        response.delete_cookie(key="must_change_password")


def _clear_auth_cookies(response: JSONResponse) -> None:
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    response.delete_cookie(key="must_change_password")


@router.get("/setup-status")
async def setup_status(auth_service: AuthServiceDep) -> SetupStatusResponse:
    """Check whether first-run setup already happened."""
    return SetupStatusResponse(setup_complete=await auth_service.get_setup_status())


@router.post("/setup", response_model=AuthSessionResponse)
async def setup(
    request: Request,
    body: FirstRunSetupRequest,
    auth_service: AuthServiceDep,
    rate_limiter: RateLimiterDep,
) -> JSONResponse:
    """Create first HR account during fresh deploy."""
    client_ip = request.client.host if request.client else "unknown"
    allowed = await rate_limiter.check_rate_limit(client_ip)
    if not allowed:
        raise RateLimitExceededError()

    result = await auth_service.setup_first_run(
        body.organization_name, body.name, body.email, body.password
    )
    response = JSONResponse(
        content={
            "user": UserResponse(
                id=result.user.id,
                email=result.user.email,
                name=result.user.name,
                avatar_url=result.user.avatar_url,
                employee_id=getattr(result.user, "employee_id", None),
                role=result.user.role,
                must_change_password=result.must_change_password,
                gmail_grant_valid=False,
                calendar_grant_valid=False,
                created_at=result.user.created_at,
                last_login=result.user.last_login,
            ).model_dump(mode="json"),
            "must_change_password": result.must_change_password,
            "setup_complete": True,
        }
    )
    _set_session_cookies(
        response,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        must_change_password=result.must_change_password,
    )
    return response


@router.post("/login", response_model=AuthSessionResponse)
async def local_login(
    request: Request,
    body: AuthLoginRequest,
    auth_service: AuthServiceDep,
    rate_limiter: RateLimiterDep,
) -> JSONResponse:
    """Local email/password login."""
    client_ip = request.client.host if request.client else "unknown"
    allowed = await rate_limiter.check_rate_limit(client_ip)
    if not allowed:
        raise RateLimitExceededError()

    result = await auth_service.login(body.email, body.password)
    response = JSONResponse(
        content={
            "user": UserResponse(
                id=result.user.id,
                email=result.user.email,
                name=result.user.name,
                avatar_url=result.user.avatar_url,
                employee_id=getattr(result.user, "employee_id", None),
                role=result.user.role,
                must_change_password=result.must_change_password,
                gmail_grant_valid=False,
                calendar_grant_valid=False,
                created_at=result.user.created_at,
                last_login=result.user.last_login,
            ).model_dump(mode="json"),
            "must_change_password": result.must_change_password,
            "setup_complete": True,
        }
    )
    _set_session_cookies(
        response,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        must_change_password=result.must_change_password,
    )
    return response


@router.post("/change-password", response_model=AuthSessionResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> JSONResponse:
    """Change current password and refresh session."""
    result = await auth_service.change_password(
        current_user, body.current_password, body.new_password
    )
    response = JSONResponse(
        content={
            "user": UserResponse(
                id=result.user.id,
                email=result.user.email,
                name=result.user.name,
                avatar_url=result.user.avatar_url,
                employee_id=getattr(result.user, "employee_id", None),
                role=result.user.role,
                must_change_password=result.must_change_password,
                gmail_grant_valid=False,
                calendar_grant_valid=False,
                created_at=result.user.created_at,
                last_login=result.user.last_login,
            ).model_dump(mode="json"),
            "must_change_password": result.must_change_password,
            "setup_complete": True,
        }
    )
    _set_session_cookies(
        response,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        must_change_password=result.must_change_password,
    )
    return response


@router.post("/refresh")
async def refresh(
    request: Request,
    token_service: TokenServiceDep,
) -> JSONResponse:
    """Refresh the access token using the refresh token cookie.

    Extracts the refresh_token from the request cookies, validates it,
    and issues a new access_token cookie if the refresh token is valid.

    Args:
        request: The incoming FastAPI request object.
        token_service: The TokenService for token refresh.

    Returns:
        A JSON response with a success message and a new access_token
        cookie set.

    Raises:
        InvalidTokenError: If the refresh token is missing, expired,
            or revoked.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise InvalidTokenError()

    new_access_token = await token_service.refresh_access_token(refresh_token)

    response = JSONResponse(content={"message": "Token refreshed"})

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        max_age=_ACCESS_TOKEN_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return response


@router.post("/logout")
async def logout(
    request: Request,
    auth_service: AuthServiceDep,
) -> JSONResponse:
    """Revoke the refresh token and clear all session cookies.

    Extracts the refresh_token from the request cookies, revokes it
    in the database, and clears the access_token, refresh_token, and
    forced password-change cookies.

    Args:
        request: The incoming FastAPI request object.
        auth_service: The AuthService for logout handling.

    Returns:
        A JSON response confirming logout with cookies cleared.
    """
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await auth_service.logout(refresh_token)

    response = JSONResponse(content={"message": "Logged out"})

    _clear_auth_cookies(response)

    return response


@router.get("/me")
async def me(
    current_user: CurrentUserDep,
    oauth_service: OAuthServiceDep,
    session: Session = Depends(get_session),
) -> UserResponse:
    """Get the current authenticated user's profile with grant status.

    Combines the user entity data with the current OAuth grant status
    to provide a complete profile response including Gmail and Calendar
    grant validity.

    Args:
        current_user: The authenticated User entity from the JWT.
        oauth_service: The OAuthService for grant status lookup.

    Returns:
        A UserResponse containing user profile and grant status.
    """
    grant_status = await _get_user_grant_status(current_user, oauth_service)
    employee = session.exec(select(Employee).where(Employee.email == current_user.email)).first()
    employee_id = current_user.employee_id or (employee.id if employee else None)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        employee_id=employee_id,
        role=current_user.role,
        must_change_password=current_user.must_change_password,
        gmail_grant_valid=grant_status.gmail_grant_valid,
        calendar_grant_valid=grant_status.calendar_grant_valid,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.get("/grant-status")
async def grant_status(
    current_user: CurrentUserDep,
    oauth_service: OAuthServiceDep,
) -> GrantStatusResponse:
    """Check the current Gmail and Calendar grant validity.

    Retrieves the user's OAuth grant from the database and determines
    whether the required Gmail and Calendar scopes are still valid.

    Args:
        current_user: The authenticated User entity from the JWT.
        oauth_service: The OAuthService for grant status lookup.

    Returns:
        A GrantStatusResponse indicating grant validity.
    """
    status = await _get_user_grant_status(current_user, oauth_service)

    return GrantStatusResponse(
        gmail_grant_valid=status.gmail_grant_valid,
        calendar_grant_valid=status.calendar_grant_valid,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_user_grant_status(user: User, oauth_service: OAuthService) -> GrantStatusResponse:
    """Retrieve the OAuth grant status for a user.

    Looks up the user's OAuth grant and determines which scopes are
    currently valid. If no grant exists or the grant is marked invalid,
    both gmail and calendar grants are reported as invalid.

    Args:
        user: The User entity to check grants for.
        oauth_service: The OAuthService with grant repository access.

    Returns:
        A GrantStatusResponse with the current grant validity.
    """
    grant = await oauth_service._grant_repository.get_by_user_id(user.id)

    if grant is None or not grant.is_valid:
        return GrantStatusResponse(
            gmail_grant_valid=False,
            calendar_grant_valid=False,
        )

    status = oauth_service.determine_grant_status(grant.scopes)
    return GrantStatusResponse(
        gmail_grant_valid=status.gmail_grant_valid,
        calendar_grant_valid=status.calendar_grant_valid,
    )
