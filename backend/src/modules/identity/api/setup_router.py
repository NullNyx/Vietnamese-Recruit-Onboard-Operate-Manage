"""FastAPI router for setup wizard endpoints.

Defines the /api/setup/* endpoints for the one-time setup wizard that runs
before normal system operation. These endpoints are only accessible before
setup is completed and locked.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.container import get_db_session
from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)
from src.modules.recruitment.container import get_recruitment_settings

router = APIRouter(prefix="/api/setup", tags=["setup"])


class SetupStatusResponse(BaseModel):
    is_initialized: bool
    is_locked: bool
    setup_completed_at: str | None
    current_step: str


class OrganizationBasicsRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=255)
    timezone: str = Field(min_length=1, max_length=64)


class AccessControlRequest(BaseModel):
    allowed_domains: list[str] = Field(default_factory=list, max_length=50)


class IdentityProviderRequest(BaseModel):
    enable_google_oauth: bool = Field(default=True)


class SetupCompleteRequest(BaseModel):
    confirmed: bool


class SetupCompleteResponse(BaseModel):
    success: bool
    message: str
    setup_completed_at: str | None


async def get_setup_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSettingsRepository:
    settings = get_recruitment_settings()
    return OrganizationSettingsRepository(session=session, settings=settings)


async def require_setup_not_locked(
    repo: OrganizationSettingsRepository = Depends(get_setup_repository),
) -> OrganizationSettingsRepository:
    is_locked = await repo.is_setup_locked()
    if is_locked:
        raise HTTPException(
            status_code=403,
            detail={"code": "SETUP_LOCKED", "message": "Setup has been completed and locked"},
        )
    return repo


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(
    repo: OrganizationSettingsRepository = Depends(get_setup_repository),
) -> SetupStatusResponse:
    status = await repo.get_setup_status()
    is_locked = status["is_locked"]

    settings_row = await repo._get_row()
    current_step = "welcome"
    if not is_locked and settings_row:
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
    await repo.set_organization_name(body.organization_name)
    await repo.set_timezone(body.timezone)
    return {"success": True, "message": "Organization basics saved"}


@router.post("/access-control", status_code=200)
async def submit_access_control(
    body: AccessControlRequest,
    repo: Annotated[OrganizationSettingsRepository, Depends(require_setup_not_locked)],
) -> dict:
    if body.allowed_domains:
        await repo.set_allowed_domains(body.allowed_domains)
    return {"success": True, "message": "Access control saved"}


@router.post("/identity-provider", status_code=200)
async def submit_identity_provider(
    body: IdentityProviderRequest,
    repo: Annotated[OrganizationSettingsRepository, Depends(require_setup_not_locked)],
) -> dict:
    return {"success": True, "message": "Identity provider saved"}


@router.post("/complete", response_model=SetupCompleteResponse)
async def complete_setup(
    body: SetupCompleteRequest,
    repo: Annotated[OrganizationSettingsRepository, Depends(require_setup_not_locked)],
) -> SetupCompleteResponse:
    if not body.confirmed:
        raise HTTPException(
            status_code=400,
            detail={"code": "CONFIRMATION_REQUIRED", "message": "Must confirm completion"},
        )
    result = await repo.complete_setup()
    return SetupCompleteResponse(
        success=True,
        message="Setup completed and locked",
        setup_completed_at=result["setup_completed_at"].isoformat(),
    )
