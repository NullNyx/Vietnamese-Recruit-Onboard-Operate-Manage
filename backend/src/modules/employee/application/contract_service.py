"""Application service for Contract lifecycle management."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.modules.employee.domain.contract import Contract
from src.modules.employee.domain.exceptions import (
    ContractAlreadyActiveError,
    ContractNotFoundError,
    ContractStatusTransitionError,
)

if TYPE_CHECKING:
    from src.modules.employee.application.employment_event_service import (
        EmploymentEventService,
    )
    from src.modules.employee.infrastructure.contract_repository import (
        ContractRepository,
    )


class ContractService:
    """Handles Contract business logic and lifecycle transitions."""

    def __init__(
        self,
        contract_repo: ContractRepository,
        event_service: EmploymentEventService,
    ) -> None:
        self._contract_repo = contract_repo
        self._event_service = event_service

    async def list_by_employee(self, employee_id: UUID) -> list[Contract]:
        return await self._contract_repo.list_by_employee(employee_id)

    async def get_by_id(self, contract_id: UUID) -> Contract:
        contract = await self._contract_repo.get_by_id(contract_id)
        if contract is None:
            raise ContractNotFoundError()
        return contract

    async def create_contract(
        self, data: dict[str, Any], created_by: UUID, actor_id: UUID | None = None
    ) -> Contract:
        contract = Contract(
            employee_id=data["employee_id"],
            contract_type=data["contract_type"],
            contract_number=data.get("contract_number"),
            template_id=data.get("template_id"),
            content=data.get("content"),
            file_path=data.get("file_path"),
            started_on=data.get("started_on"),
            ended_on=data.get("ended_on"),
            created_by=created_by,
        )
        contract = await self._contract_repo.create(contract)
        actor = actor_id or created_by
        await self._event_service.record(
            employee_id=contract.employee_id,
            event_type="contract_update",
            actor_hr_id=actor,
            after={"contract_id": str(contract.id), "status": "draft"},
            note=f"Contract {contract.contract_type} created",
        )
        return contract

    async def update_draft(self, contract_id: UUID, data: dict[str, Any]) -> Contract:
        contract = await self.get_by_id(contract_id)
        if contract.status not in ("draft", "pending_signature"):
            raise ContractAlreadyActiveError()
        updated = await self._contract_repo.update(contract_id, data)
        if updated is None:
            raise ContractNotFoundError()
        return updated

    async def mark_sending(self, contract_id: UUID, actor_id: UUID) -> Contract:
        contract = await self.get_by_id(contract_id)
        if contract.status != "draft":
            raise ContractStatusTransitionError()
        return await self._change_status(contract, "pending_signature", actor_id)

    async def sign(
        self,
        contract_id: UUID,
        actor_id: UUID,
        signed_doc_path: str | None = None,
        signed_on: date | None = None,
    ) -> Contract:
        contract = await self.get_by_id(contract_id)
        if contract.status != "pending_signature":
            raise ContractStatusTransitionError()
        update: dict[str, Any] = {"status": "active"}
        if signed_doc_path:
            update["signed_document_path"] = signed_doc_path
        if signed_on:
            update["signed_on"] = signed_on
        updated = await self._contract_repo.update(contract_id, update)
        if updated is None:
            raise ContractNotFoundError()
        await self._event_service.record(
            employee_id=contract.employee_id,
            event_type="contract_update",
            actor_hr_id=actor_id,
            before={"contract_id": str(contract.id), "status": "pending_signature"},
            after={"contract_id": str(contract.id), "status": "active"},
        )
        return updated

    async def terminate(self, contract_id: UUID, actor_id: UUID) -> Contract:
        contract = await self.get_by_id(contract_id)
        if contract.status in ("terminated", "cancelled", "expired"):
            raise ContractStatusTransitionError()
        return await self._change_status(contract, "terminated", actor_id)

    async def cancel(self, contract_id: UUID, actor_id: UUID) -> Contract:
        contract = await self.get_by_id(contract_id)
        if contract.status in ("terminated", "cancelled", "expired"):
            raise ContractStatusTransitionError()
        return await self._change_status(contract, "cancelled", actor_id)

    async def renew(
        self,
        contract_id: UUID,
        actor_id: UUID,
        new_started_on: date | None = None,
        new_ended_on: date | None = None,
        new_content: str | None = None,
    ) -> Contract:
        """Renew an active contract by re-creating it with updated dates."""
        contract = await self.get_by_id(contract_id)
        if contract.status != "active":
            raise ContractStatusTransitionError()
        update: dict[str, Any] = {"status": "expired"}
        if new_ended_on:
            update["ended_on"] = new_ended_on
        await self._contract_repo.update(contract_id, update)
        # Create new contract as follow-on
        new_data = {
            "employee_id": contract.employee_id,
            "contract_type": contract.contract_type,
            "contract_number": contract.contract_number,
            "template_id": contract.template_id,
            "content": new_content or contract.content,
            "file_path": contract.file_path,
            "started_on": new_started_on,
            "ended_on": new_ended_on,
        }
        return await self.create_contract(new_data, actor_id)

    async def _change_status(self, contract: Contract, new_status: str, actor_id: UUID) -> Contract:
        old_status = contract.status
        updated = await self._contract_repo.update(contract.id, {"status": new_status})
        if updated is None:
            raise ContractNotFoundError()
        await self._event_service.record(
            employee_id=contract.employee_id,
            event_type="contract_update",
            actor_hr_id=actor_id,
            before={"contract_id": str(contract.id), "status": old_status},
            after={"contract_id": str(contract.id), "status": new_status},
        )
        return updated
