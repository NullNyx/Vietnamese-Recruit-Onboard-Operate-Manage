"""Application service for ContractTemplate CRUD."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.modules.employee.domain.contract_template import ContractTemplate
from src.modules.employee.domain.exceptions import EmployeeError

if TYPE_CHECKING:
    from src.modules.employee.infrastructure.contract_template_repository import (
        ContractTemplateRepository,
    )


class ContractTemplateService:
    """Handles ContractTemplate business logic."""

    def __init__(self, template_repo: ContractTemplateRepository) -> None:
        self._template_repo = template_repo

    async def list_active(self) -> list[ContractTemplate]:
        return await self._template_repo.list_active()

    async def get_by_id(self, template_id: UUID) -> ContractTemplate:
        template = await self._template_repo.get_by_id(template_id)
        if template is None:
            raise EmployeeError("Contract template not found")
        return template

    async def create(self, data: dict[str, Any], created_by: UUID) -> ContractTemplate:
        template = ContractTemplate(
            name=data["name"],
            content=data["content"],
            file_path=data.get("file_path"),
            created_by=created_by,
        )
        return await self._template_repo.create(template)

    async def update(
        self, template_id: UUID, data: dict[str, Any]
    ) -> ContractTemplate:
        template = await self._template_repo.update(template_id, data)
        if template is None:
            raise EmployeeError("Contract template not found")
        return template

    async def archive(self, template_id: UUID) -> ContractTemplate:
        template = await self._template_repo.archive(template_id)
        if template is None:
            raise EmployeeError("Contract template not found")
        return template
