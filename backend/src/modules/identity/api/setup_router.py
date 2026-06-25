"""FastAPI router for the first-run setup wizard.

Defines the /api/setup/* endpoints for initializing the system configuration.
These endpoints are only accessible when the system is not yet set up.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from src.modules.identity.application.setup_service import SetupService
from src.modules.identity.container import get_setup_service

setup_router = APIRouter(prefix="/api/setup", tags=["setup"])


@setup_router.get("/status")
async def get_setup_status(
    setup_service: SetupService = Depends(get_setup_service),
) -> dict[str, bool]:
    """Check if the system setup is completed."""
    is_completed = await setup_service.is_setup_completed()
    return {"is_setup_completed": is_completed}


class VerifyTokenRequest(BaseModel):
    """Request model for verifying a setup token."""
    
    token: str


@setup_router.post("/verify")
async def verify_setup_token(
    request: VerifyTokenRequest,
    response: Response,
    setup_service: SetupService = Depends(get_setup_service),
) -> dict[str, str]:
    """Verify the setup token and issue a setup session cookie.

    Args:
        request: The verification request containing the token.
        response: The FastAPI response object for setting cookies.
        setup_service: The service for managing setup state.

    Returns:
        A success message.

    Raises:
        HTTPException: 401 if the token is invalid.
    """
    if await setup_service.is_setup_completed():
        raise HTTPException(
            status_code=403, 
            detail={"code": "SETUP_COMPLETED", "message": "Setup is already completed"}
        )

    is_valid = await setup_service.verify_setup_token(request.token)
    if not is_valid:
        raise HTTPException(
            status_code=401, 
            detail={"code": "INVALID_TOKEN", "message": "Invalid setup token"}
        )

    response.set_cookie(
        key="setup_session",
        value="valid_session_dummy",
        httponly=True,
        samesite="lax",
    )
    return {"message": "Token verified successfully"}


# --- Configuration Endpoints ---

from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.identity.container import require_setup_session, get_db_session
from src.modules.recruitment.infrastructure.org_settings_repository import OrganizationSettingsRepository


async def get_org_settings_repo(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSettingsRepository:
    """Provide an OrganizationSettingsRepository instance."""
    return OrganizationSettingsRepository(session)


class OrganizationSetupRequest(BaseModel):
    """Request model for setting up the organization timezone."""
    timezone: str


@setup_router.post(
    "/organization",
    dependencies=[Depends(require_setup_session)],
)
async def setup_organization(
    request: OrganizationSetupRequest,
    org_repo: OrganizationSettingsRepository = Depends(get_org_settings_repo),
) -> dict[str, str]:
    """Set the Organization's default timezone during setup.

    Args:
        request: The request containing the IANA timezone.
        org_repo: Repository for Organization settings.

    Returns:
        A success message with the configured timezone.

    Raises:
        HTTPException: 400 if the timezone is invalid.
    """
    try:
        await org_repo.set_timezone(request.timezone)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_TIMEZONE", "message": str(exc)},
        )
    return {"message": "Organization timezone set successfully", "timezone": request.timezone}


from src.modules.identity.container import get_whitelist_manager, get_oauth_config_manager
from src.modules.identity.application.whitelist_manager import WhitelistManager
from src.modules.identity.application.oauth_config_manager import OAuthConfigManager, OAuthConfigValidationError


class DomainSetupRequest(BaseModel):
    """Request model for setting up allowed domains."""
    domains: list[str]


class WhitelistSetupRequest(BaseModel):
    """Request model for adding the initial admin emails to whitelist."""
    emails: list[str]



class OAuthSetupRequest(BaseModel):
    """Request model for setting up Google OAuth."""
    client_id: str
    client_secret: str
    redirect_uri: str


@setup_router.post("/domains", dependencies=[Depends(require_setup_session)])
async def setup_domains(
    request: DomainSetupRequest,
    org_repo: OrganizationSettingsRepository = Depends(get_org_settings_repo),
) -> dict[str, str]:
    """Configure allowed login domains for the organization."""
    try:
        await org_repo.set_allowed_domains(request.domains)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, 
            detail={"code": "INVALID_DOMAINS", "message": str(exc)}
        )
    return {"message": "Allowed domains configured successfully"}


@setup_router.post("/whitelist", dependencies=[Depends(require_setup_session)])
async def setup_whitelist(
    request: WhitelistSetupRequest,
    whitelist_manager: WhitelistManager = Depends(get_whitelist_manager),
) -> dict[str, str]:
    """Add the initial admin emails to the whitelist."""
    for email in request.emails:
        try:
            # admin is None since the system is not yet initialized and no admin user exists
            await whitelist_manager.add_entry(value=email, admin=None)
        except HTTPException as exc:
            if exc.status_code == 409:
                continue
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=400, 
                detail={"code": "INVALID_WHITELIST_ENTRY", "message": str(exc)}
            )
    return {"message": "Admin whitelist configured successfully"}



@setup_router.post("/oauth", dependencies=[Depends(require_setup_session)])
async def setup_oauth(
    request: OAuthSetupRequest,
    oauth_manager: OAuthConfigManager = Depends(get_oauth_config_manager),
) -> dict[str, str]:
    """Configure Google OAuth credentials."""
    try:
        await oauth_manager.update_config(
            client_id=request.client_id,
            client_secret=request.client_secret,
            redirect_uri=request.redirect_uri,
            admin=None,
        )
    except OAuthConfigValidationError as exc:
        raise HTTPException(
            status_code=400, 
            detail={"code": "OAUTH_VALIDATION_FAILED", "message": exc.message}
        )
    return {"message": "Google OAuth credentials configured successfully"}


@setup_router.post("/lock", dependencies=[Depends(require_setup_session)])
async def setup_lock(
    response: Response,
    setup_service: SetupService = Depends(get_setup_service),
) -> dict[str, str]:
    """Lock the setup wizard and complete the initialization."""
    try:
        await setup_service.lock_setup()
    except ValueError as exc:
        raise HTTPException(
            status_code=400, 
            detail={"code": "SETUP_ERROR", "message": str(exc)}
        )

    response.delete_cookie("setup_session", httponly=True, samesite="lax")
    return {"message": "System setup is now locked and complete"}
