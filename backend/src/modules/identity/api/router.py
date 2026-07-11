"""FastAPI router for the Identity & Auth module.

Defines the /api/auth/* endpoints for first-run setup, local login,
password change, token refresh, logout, and user profile retrieval.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select

from src.modules.employee.domain.entities import Employee
from src.modules.identity.api.admin_router import require_admin
from src.modules.identity.api.schemas import (
    AuthLoginRequest,
    AuthSessionResponse,
    ChangePasswordRequest,
    FirstRunSetupRequest,
    GoogleWorkspaceCallbackRequest,
    GoogleWorkspaceConnectionResponse,
    GrantStatusResponse,
    OAuthConfigUpdateRequest,
    SetupStatusResponse,
    UserResponse,
)
from src.modules.identity.application.auth_service import AuthService
from src.modules.identity.application.oauth_config_manager import OAuthConfigManager
from src.modules.identity.application.oauth_service import OAuthService
from src.modules.identity.application.organization_google_connection_service import (
    OrganizationGoogleConnectionService,
)
from src.modules.identity.application.token_service import TokenService
from src.modules.identity.container import (
    get_auth_service,
    get_crypto_utils,
    get_current_user,
    get_db_session,
    get_jwt_utils,
    get_oauth_config_manager,
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
AdminOnlyDep = Annotated[User, Depends(require_admin)]
OAuthConfigManagerDep = Annotated[OAuthConfigManager, Depends(get_oauth_config_manager)]

# Compatibility alias for router tests and older dependency overrides.
get_session = get_db_session

# ---------------------------------------------------------------------------
# Google connection dependency helper
# ---------------------------------------------------------------------------


async def _get_connection_service(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationGoogleConnectionService:
    from httpx import AsyncClient

    from src.modules.identity.application.audit_service import AuditService
    from src.modules.identity.infrastructure.audit_log_repository import AuditLogRepository
    from src.modules.identity.infrastructure.connection_state_repository import (
        OrganizationGoogleConnectionRepository,
    )
    from src.modules.identity.infrastructure.oauth_config_repository import OAuthConfigRepository
    from src.modules.identity.infrastructure.oauth_grant_repository import OAuthGrantRepository
    from src.modules.recruitment.infrastructure.org_settings_repository import (
        OrganizationSettingsRepository,
    )

    audit_log_repo = AuditLogRepository(session)

    return OrganizationGoogleConnectionService(
        connection_repo=OrganizationGoogleConnectionRepository(session),
        oauth_config_repo=OAuthConfigRepository(session),
        oauth_grant_repo=OAuthGrantRepository(session),
        audit_service=AuditService(repository=audit_log_repo),
        crypto=get_crypto_utils(),
        state_jwt=get_jwt_utils(),
        org_settings_repo=OrganizationSettingsRepository(session),
        http_client=AsyncClient(),
    )


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


@router.post("/organization-google-connection")
async def save_google_connection_config(
    body: OAuthConfigUpdateRequest,
    current_user: AdminOnlyDep,
    manager: OAuthConfigManagerDep,
    connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
) -> GoogleWorkspaceConnectionResponse:
    await manager.update_config(
        client_id=body.client_id,
        client_secret=body.client_secret,
        redirect_uri=body.redirect_uri,
        admin=current_user,
    )
    res = await connection_service.get_status()
    return GoogleWorkspaceConnectionResponse(**res.__dict__)


@router.get("/organization-google-connection/authorize-url")
async def authorize_google_connection(
    current_user: AdminOnlyDep,
    connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
) -> GoogleWorkspaceConnectionResponse:
    res = await connection_service.initiate(current_user)
    return GoogleWorkspaceConnectionResponse(**res.__dict__)


@router.get("/organization-google-connection")
async def get_google_connection(
    current_user: AdminOnlyDep,
    connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
) -> GoogleWorkspaceConnectionResponse:
    res = await connection_service.get_status()
    return GoogleWorkspaceConnectionResponse(**res.__dict__)


@router.post("/organization-google-connection/reconnect")
async def reconnect_google_connection(
    current_user: AdminOnlyDep,
    connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
) -> GoogleWorkspaceConnectionResponse:
    res = await connection_service.initiate(current_user)
    return GoogleWorkspaceConnectionResponse(**res.__dict__)


@router.post("/organization-google-connection/callback")
async def callback_google_connection(
    body: GoogleWorkspaceCallbackRequest,
    current_user: AdminOnlyDep,
    connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
) -> GoogleWorkspaceConnectionResponse:
    res = await connection_service.callback(hr=current_user, state=body.state, code=body.code)
    return GoogleWorkspaceConnectionResponse(**res.__dict__)

    @router.delete("/organization-google-connection")
    async def disconnect_google_connection(
        current_user: AdminOnlyDep,
        connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
    ) -> GoogleWorkspaceConnectionResponse:
        res = await connection_service.disconnect(current_user)
        return GoogleWorkspaceConnectionResponse(**res.__dict__)

    # ---------------------------------------------------------------------------
    # Calendar list + selection (Issue 154)
    # ---------------------------------------------------------------------------

    class CalendarEntryResponse(BaseModel):
        """A single calendar list entry."""

        model_config = ConfigDict(from_attributes=True)

        id: str
        summary: str
        description: str | None = None
        primary: bool = False
        access_role: str = ""

    class CalendarListResponseSchema(BaseModel):
        """Response for the calendar list endpoint."""

        calendars: list[CalendarEntryResponse]
        selected_calendar_id: str | None = None

    class SelectCalendarRequest(BaseModel):
        """Request to select a calendar for interview scheduling."""

        calendar_id: str

    @router.get("/organization-google-connection/calendars")
    async def list_calendars_for_selection(
        current_user: AdminOnlyDep,
        connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
    ) -> CalendarListResponseSchema:
        """List available calendars and the currently selected one.

        Returns calendars the Organization Google Connection has writer access to,
        along with the currently selected calendar ID (if any).
        """

        # Get the current connection to read selected_calendar_id
        from src.modules.identity.container import get_db_session
        from src.modules.identity.infrastructure.connection_state_repository import (
            OrganizationGoogleConnectionRepository,
        )

        session = await get_db_session().__anext__()
        conn_repo = OrganizationGoogleConnectionRepository(session)
        current_conn = await conn_repo.get_singleton()
        selected_calendar_id = current_conn.selected_calendar_id if current_conn else None

        calendars = await connection_service.list_calendars(current_user)
        entries = [
            CalendarEntryResponse(
                id=cal["id"],
                summary=cal.get("summary", cal["id"]),
                description=cal.get("description"),
                primary=cal.get("primary", False),
                access_role=cal.get("accessRole", ""),
            )
            for cal in calendars
        ]
        return CalendarListResponseSchema(
            calendars=entries, selected_calendar_id=selected_calendar_id
        )

    @router.put("/organization-google-connection/selected-calendar", status_code=204)
    async def save_selected_calendar(
        body: SelectCalendarRequest,
        current_user: AdminOnlyDep,
        connection_service: OrganizationGoogleConnectionService = Depends(_get_connection_service),
    ) -> None:
        """Save the selected calendar ID for interview scheduling."""
        await connection_service.update_selected_calendar(
            calendar_id=body.calendar_id,
            hr=current_user,
        )


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
    """Refresh access token using refresh token cookie."""
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
    """Revoke refresh token and clear session cookies."""
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
    """Get current authenticated user's profile with grant status."""
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
    """Check current Gmail and Calendar grant validity."""
    status = await _get_user_grant_status(current_user, oauth_service)
    return GrantStatusResponse(
        gmail_grant_valid=status.gmail_grant_valid,
        calendar_grant_valid=status.calendar_grant_valid,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_user_grant_status(user: User, oauth_service: OAuthService) -> GrantStatusResponse:
    """Retrieve OAuth grant status for a user."""
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
