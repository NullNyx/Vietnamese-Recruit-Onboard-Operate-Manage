"""API routes for onboarding template management."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.modules.identity.api.admin_router import AdminUserDep
from src.modules.onboarding.api.template_schemas import (
    OnboardingTemplateCreateRequest,
    OnboardingTemplateListResponse,
    OnboardingTemplatePreviewResponse,
    OnboardingTemplateResponse,
    OnboardingTemplateType,
    OnboardingTemplateUpdateRequest,
)
from src.modules.onboarding.application.template_service import OnboardingTemplateService
from src.modules.onboarding.domain.entities import OnboardingTemplate
from src.modules.onboarding.template_container import get_onboarding_template_service

template_router = APIRouter(prefix="/api/onboarding/templates", tags=["onboarding-templates"])


def _as_response(template: OnboardingTemplate) -> OnboardingTemplateResponse:
    return OnboardingTemplateResponse.model_validate(template)


@template_router.get("", response_model=OnboardingTemplateListResponse)
async def list_templates(
    _admin: AdminUserDep,
    template_type: OnboardingTemplateType | None = Query(default=None),
    include_archived: bool = False,
    service: OnboardingTemplateService = Depends(get_onboarding_template_service),
) -> OnboardingTemplateListResponse:
    items = await service.list_templates(template_type, include_archived)
    return OnboardingTemplateListResponse(items=[_as_response(item) for item in items])


@template_router.post("", response_model=OnboardingTemplateResponse)
async def create_template(
    actor: AdminUserDep,
    body: OnboardingTemplateCreateRequest,
    service: OnboardingTemplateService = Depends(get_onboarding_template_service),
) -> OnboardingTemplateResponse:
    template = await service.create_template(actor, body.model_dump())
    return _as_response(template)


@template_router.patch("/{template_id}", response_model=OnboardingTemplateResponse)
async def update_template(
    actor: AdminUserDep,
    template_id: UUID,
    body: OnboardingTemplateUpdateRequest,
    service: OnboardingTemplateService = Depends(get_onboarding_template_service),
) -> OnboardingTemplateResponse:
    try:
        template = await service.update_template(
            template_id, actor, body.model_dump(exclude_unset=True)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _as_response(template)


@template_router.post("/{template_id}/archive", response_model=OnboardingTemplateResponse)
async def archive_template(
    actor: AdminUserDep,
    template_id: UUID,
    service: OnboardingTemplateService = Depends(get_onboarding_template_service),
) -> OnboardingTemplateResponse:
    try:
        template = await service.archive_template(template_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _as_response(template)


@template_router.get("/{template_id}/preview", response_model=OnboardingTemplatePreviewResponse)
async def preview_template(
    template_id: UUID,
    _admin: AdminUserDep,
    service: OnboardingTemplateService = Depends(get_onboarding_template_service),
) -> OnboardingTemplatePreviewResponse:
    try:
        return OnboardingTemplatePreviewResponse(**await service.preview_template(template_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
