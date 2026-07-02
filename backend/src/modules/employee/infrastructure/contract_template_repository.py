"""Repository for ContractTemplate entity CRUD operations."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.employee.domain.contract_template import ContractTemplate


class ContractTemplateRepository:
    """Handles ContractTemplate persistence using async SQLAlchemy sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, template: ContractTemplate) -> ContractTemplate:
        self._session.add(template)
        await self._session.flush()
        return template

    async def get_by_id(self, template_id: UUID) -> ContractTemplate | None:
        stmt = select(ContractTemplate).where(ContractTemplate.id == template_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_active(self) -> list[ContractTemplate]:
        stmt = (
            select(ContractTemplate)
            .where(ContractTemplate.status == "active")
            .order_by(ContractTemplate.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, template_id: UUID, data: dict[str, Any]) -> ContractTemplate | None:
        stmt = select(ContractTemplate).where(ContractTemplate.id == template_id)
        result = await self._session.execute(stmt)
        template = result.scalars().first()

        if template is None:
            return None

        for key, value in data.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.now(UTC)
        self._session.add(template)
        await self._session.flush()
        return template

    async def archive(self, template_id: UUID) -> ContractTemplate | None:
        stmt = select(ContractTemplate).where(ContractTemplate.id == template_id)
        result = await self._session.execute(stmt)
        template = result.scalars().first()

        if template is None:
            return None

        template.status = "archived"
        template.updated_at = datetime.now(UTC)
        self._session.add(template)
        await self._session.flush()
        return template
