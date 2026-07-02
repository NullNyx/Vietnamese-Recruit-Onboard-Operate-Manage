"""Application service for ContractAmendment CRUD."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.modules.employee.domain.contract_amendment import ContractAmendment
from src.modules.employee.domain.exceptions import EmployeeError

if TYPE_CHECKING:
    from src.modules.employee.infrastructure.contract_amendment_repository import (
        ContractAmendmentRepository,
    )


class ContractAmendmentService:
    """Handles ContractAmendment business logic."""

    def __init__(self, amendment_repo: ContractAmendmentRepository) -> None:
        self._amendment_repo = amendment_repo

    async def create(self, data: dict[str, Any], created_by: UUID) -> ContractAmendment:
        amendment = ContractAmendment(
            contract_id=data["contract_id"],
            name=data["name"],
            content=data["content"],
            file_path=data.get("file_path"),
            created_by=created_by,
        )
        return await self._amendment_repo.create(amendment)

    async def list_by_contract(self, contract_id: UUID) -> list[ContractAmendment]:
        return await self._amendment_repo.list_by_contract(contract_id)

    async def update(self, amendment_id: UUID, data: dict[str, Any]) -> ContractAmendment:
        amendment = await self._amendment_repo.update(amendment_id, data)
        if amendment is None:
            raise EmployeeError("Contract amendment not found")
        return amendment
