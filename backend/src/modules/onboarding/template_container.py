"""Dependency wiring for onboarding template management."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.container import get_db_session
from src.modules.onboarding.application.template_service import OnboardingTemplateService
from src.modules.onboarding.infrastructure.audit_repository import OnboardingAuditRepository
from src.modules.onboarding.infrastructure.template_repository import OnboardingTemplateRepository


async def get_onboarding_template_service(
    session: AsyncSession = Depends(get_db_session),
) -> OnboardingTemplateService:
    return OnboardingTemplateService(
        template_repo=OnboardingTemplateRepository(session),
        audit_repo=OnboardingAuditRepository(session),
        session=session,
    )
