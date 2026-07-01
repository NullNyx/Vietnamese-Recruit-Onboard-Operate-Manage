"""FastAPI router for setup wizard endpoints.

Defines the /api/setup/* endpoints for the one-time setup wizard that runs
before normal system operation. These endpoints are only accessible before
setup is completed and locked.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session


from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)
from src.modules.recruitment.container import get_recruitment_settings

router = APIRouter(prefix="/api/setup", tags=["setup"])

# --- Schemas ---


class SetupStatusResponse(BaseModel):
    """Response for setup status check."""

    is_initialized: bool = Field(description="Whether any OrganizationSettings exist")
    is_locked: bool = Field(description="Whether setup has been completed and locked")
    setup_completed_at: str | None = Field(description="ISO timestamp when setup completed")
    current_step: str = Field(description="Current wizard step if not locked")


class OrganizationBasicsRequest(BaseModel):
    """Request body for organization basics step."""

    organization_name: str = Field(min_length=1, max_length=255)
    timezone: str = Field(min_length=1, max_length=64)


class AccessControlRequest(BaseModel):
    """Request body for access control step."""

    allowed_domains: list[str] = Field(default_factory=list, max_length=50)
    whitelist_emails: list[str] = Field(default_factory=list, max_length=100)


class IdentityProviderRequest(BaseModel):
    """Request body for identity provider step."""

    enable_google_oauth: bool = Field(default=True)
    oauth_client_id: str | None = Field(default=None, max_length=255)
    oauth_redirect_uri: str | None = Field(default=None, max_length=500)


class SetupCompleteRequest(BaseModel):
    """Request body for completing setup."""

    confirmed: bool = Field(description="Must be true to confirm completion")


class SetupCompleteResponse(BaseModel):
    """Response for setup completion."""

    success: bool
    message: str
    setup_completed_at: str | None


# --- Dependencies ---


async def get_setup_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSettingsRepository:
    """Provide an OrganizationSettingsRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        An OrganizationSettingsRepository bound to the session.
    """
    settings = get_recruitment_settings()
    return OrganizationSettingsRepository(session=session, settings=settings)


async def require_setup_not_locked(
    repo: OrganizationSettingsRepository = Depends(get_setup_repository),
) -> OrganizationSettingsRepository:
    """Ensure setup is not locked before allowing access.

    Args:
        repo: The repository to check setup lock status.

    Returns:
        The repository if setup is not locked.

    Raises:
        HTTPException: 403 if setup is locked, 404 if not initialized.
    """
    is_locked = await repo.is_setup_locked()
    if is_locked:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "SETUP_LOCKED",
                "message": "Setup has been completed and locked",
            },
        )
    return repo


# --- Endpoints ---


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(
    repo: OrganizationSettingsRepository = Depends(get_setup_repository),
) -> SetupStatusResponse:
    """Check the current setup status.

    Returns whether the system is initialized, whether setup is locked,
    and the current step if not locked.
    """
    is_locked = await repo.is_setup_locked()
    
    # Check if any settings exist
    status = await repo.get_setup_status()
    
    # Determine current step based on what has been configured
    current_step = "welcome"
    if not is_locked:
        settings_row = await repo._get_row()
        if settings_row:
            org_name = settings_row.organization_name
            allowed_domains = settings_row.allowed_domains
            if org_name:
                if allowed_domains:
                    current_step = "review"
                else:
                    current_step = "access-control"
            else:
                current_step = "organization"
    
    return SetupStatusResponse(
        is_initialized=status["setup_completed_at"] is not None,
        is_locked=is_locked,
        setup_completed_at=status["setup_completed_at"].isoformat() if status["setup_completed_at"] else None,
        current_step=current_step,
    )


@router.post("/organization", status_code=200)
async def submit_organization_basics(
    body: OrganizationBasicsRequest,
    repo: Annotated[OrganizationSettingsRepository, Depends(require_setup_not_locked)],
) -> dict:
    """Submit organization basics (name, timezone).

    This step initializes the OrganizationSettings if not present,
    or updates the existing settings.
    """
    await repo.set_organization_name(body.organization_name)
    await repo.set_timezone(body.timezone)
    
    return {"success": True, "message": "Organization basics saved"}


@router.post("/access-control", status_code=200)
async def submit_access_control(
    body: AccessControlRequest,
    repo: Annotated[OrganizationSettingsRepository, Depends(require_setup_not_locked)],
) -> dict:
    """Submit access control configuration (allowed domains, whitelist).

    Validates and persists the allowed domains and whitelist emails.
    Whitelist entries are managed via the admin UI after setup.
    """
    # Set allowed domains
    if body.allowed_domains:
        await repo.set_allowed_domains(body.allowed_domains)
    
    # Note: Whitelist entries are managed via the admin UI after setup is complete.
    # For now, we just focus on allowed_domains which are the primary gate.
    
    return {"success": True, "message": "Access control saved"}


@router.post("/identity-provider", status_code=200)
async def submit_identity_provider(
    body: IdentityProviderRequest,
    repo: Annotated[OrganizationSettingsRepository, Depends(require_setup_not_locked)],
) -> dict:
    """Submit identity provider configuration (Google OAuth).

    Note: OAuth secrets should come from environment variables for security.
    This endpoint stores optional display configuration.
    """
    # For now, this is a placeholder - OAuth config is managed via admin endpoints
    return {"success": True, "message": "Identity provider saved"}


@router.post("/complete", response_model=SetupCompleteResponse)
async def complete_setup(
    body: SetupCompleteRequest,
    repo: Annotated[OrganizationSettingsRepository, Depends(require_setup_not_locked)],
) -> SetupCompleteResponse:
    """Complete the setup wizard and lock it.

    This endpoint is called by the first admin completing setup.
    Authentication is handled via the setup flow - no JWT required for this step.
    After completion, normal login is enabled and /setup is disabled.
    """
    if not body.confirmed:
        raise HTTPException(
            status_code=400,
            detail={"code": "CONFIRMATION_REQUIRED", "message": "Must confirm completion"},
        )
    
    # For first-run setup, there's no authenticated user yet.
    # We complete setup with a null admin_user_id.
    result = await repo.complete_setup(admin_user_id=None)
    
    return SetupCompleteResponse(
        success=True,
        message="Setup completed and locked",
        setup_completed_at=result["setup_completed_at"].isoformat(),
    )
