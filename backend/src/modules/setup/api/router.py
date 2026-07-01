"""API routes for the initial setup wizard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.modules.setup.api.schemas import (
    AiProviderRequest,
    CreateAdminRequest,
    OrgConfigRequest,
    SetupCompleteResponse,
    SetupStatusResponse,
)
from src.modules.setup.application.setup_service import (
    SetupAlreadyCompleteError,
    SetupService,
)
from src.modules.setup.container import get_setup_service

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatusResponse)
async def status(setup_service: SetupService = Depends(get_setup_service)) -> SetupStatusResponse:
    """Return current setup progress."""
    return SetupStatusResponse(**await setup_service.get_status())


@router.post("/admin")
async def create_admin(
    body: CreateAdminRequest,
    setup_service: SetupService = Depends(get_setup_service),
) -> dict[str, str]:
    """Create first SUPER_ADMIN account."""
    try:
        user = await setup_service.create_first_admin(body.email, body.password, body.name)
    except SetupAlreadyCompleteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": str(user.id), "email": user.email, "role": user.role.value}


@router.post("/organization")
async def organization(
    body: OrgConfigRequest,
    setup_service: SetupService = Depends(get_setup_service),
) -> dict[str, str]:
    """Store company info and timezone."""
    try:
        await setup_service.configure_organization(body.name, body.tax_code, body.timezone)
    except SetupAlreadyCompleteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "ok"}


@router.post("/ai-provider")
async def ai_provider(
    body: AiProviderRequest,
    setup_service: SetupService = Depends(get_setup_service),
) -> dict[str, str]:
    """Store AI provider configuration."""
    try:
        await setup_service.configure_ai_provider(body.provider, body.api_key)
    except SetupAlreadyCompleteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "ok"}


@router.post("/complete", response_model=SetupCompleteResponse)
async def complete(
    setup_service: SetupService = Depends(get_setup_service),
) -> SetupCompleteResponse:
    """Finish setup and lock the wizard."""
    await setup_service.complete_setup()
    return SetupCompleteResponse(status="completed")
