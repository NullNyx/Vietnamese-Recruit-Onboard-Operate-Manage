"""Repository for OnboardingTemplate persistence."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.onboarding.domain.entities import OnboardingTemplate


class OnboardingTemplateRepository:
    """Handles OnboardingTemplate persistence using async SQLAlchemy sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        template_type: str | None = None,
        include_archived: bool = False,
    ) -> list[OnboardingTemplate]:
        statement = select(OnboardingTemplate)
        if template_type is not None:
            statement = statement.where(OnboardingTemplate.template_type == template_type)
        if not include_archived:
            statement = statement.where(OnboardingTemplate.is_archived == False)  # noqa: E712
        statement = statement.order_by(
            cast(Any, OnboardingTemplate.template_type),
            cast(Any, OnboardingTemplate.order_index),
            cast(Any, OnboardingTemplate.display_name),
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, template_id: UUID) -> OnboardingTemplate | None:
        statement = select(OnboardingTemplate).where(OnboardingTemplate.id == template_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_by_key(
        self,
        template_type: str,
        key: str,
        include_archived: bool = False,
    ) -> OnboardingTemplate | None:
        statement = select(OnboardingTemplate).where(
            OnboardingTemplate.template_type == template_type,
            OnboardingTemplate.key == key,
        )
        if not include_archived:
            statement = statement.where(OnboardingTemplate.is_archived == False)  # noqa: E712
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create(self, template: OnboardingTemplate) -> OnboardingTemplate:
        self.session.add(template)
        await self.session.flush()
        return template

    async def update(self, template: OnboardingTemplate) -> OnboardingTemplate:
        self.session.add(template)
        await self.session.flush()
        return template
