"""Unit tests for ContractService."""

from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.employee.application.contract_service import ContractService
from src.modules.employee.domain.contract import Contract
from src.modules.employee.domain.exceptions import (
    ContractAlreadyActiveError,
    ContractNotFoundError,
    ContractStatusTransitionError,
)


@pytest.fixture
def contract_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def event_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(contract_repo: AsyncMock, event_service: AsyncMock) -> ContractService:
    return ContractService(contract_repo=contract_repo, event_service=event_service)


class TestContractLifecycle:
    async def test_create_contract_records_event(
        self, service: ContractService, contract_repo: AsyncMock, event_service: AsyncMock
    ) -> None:
        employee_id = uuid4()
        created_by = uuid4()
        mock_contract = AsyncMock(spec=Contract)
        mock_contract.id = uuid4()
        mock_contract.employee_id = employee_id
        mock_contract.contract_type = "labor"
        contract_repo.create.return_value = mock_contract

        result = await service.create_contract(
            {"employee_id": employee_id, "contract_type": "labor"},
            created_by=created_by,
            actor_id=created_by,
        )

        assert result == mock_contract
        contract_repo.create.assert_called_once()
        created = contract_repo.create.call_args[0][0]
        assert created.employee_id == employee_id
        assert created.status == "draft"
        event_service.record.assert_awaited_once()

    async def test_mark_sending_changes_status_and_records_event(
        self, service: ContractService, contract_repo: AsyncMock, event_service: AsyncMock
    ) -> None:
        contract = AsyncMock(spec=Contract)
        contract.id = uuid4()
        contract.employee_id = uuid4()
        contract.status = "draft"
        contract_repo.get_by_id.return_value = contract
        updated = AsyncMock(spec=Contract)
        contract_repo.update.return_value = updated

        result = await service.mark_sending(contract.id, uuid4())

        assert result == updated
        contract_repo.update.assert_awaited_once_with(contract.id, {"status": "pending_signature"})
        event_service.record.assert_awaited_once()

    async def test_sign_sets_active_and_sign_fields(
        self, service: ContractService, contract_repo: AsyncMock, event_service: AsyncMock
    ) -> None:
        contract = AsyncMock(spec=Contract)
        contract.id = uuid4()
        contract.employee_id = uuid4()
        contract.status = "pending_signature"
        contract_repo.get_by_id.return_value = contract
        updated = AsyncMock(spec=Contract)
        contract_repo.update.return_value = updated

        result = await service.sign(contract.id, uuid4(), signed_doc_path="/files/signed.pdf", signed_on=date(2026, 1, 1))

        assert result == updated
        contract_repo.update.assert_awaited_once()
        update_data = contract_repo.update.call_args[0][1]
        assert update_data["status"] == "active"
        assert update_data["signed_document_path"] == "/files/signed.pdf"
        assert update_data["signed_on"] == date(2026, 1, 1)
        event_service.record.assert_awaited_once()

    async def test_renew_expires_old_and_creates_new(
        self, service: ContractService, contract_repo: AsyncMock, event_service: AsyncMock
    ) -> None:
        contract = AsyncMock(spec=Contract)
        contract.id = uuid4()
        contract.employee_id = uuid4()
        contract.contract_type = "labor"
        contract.contract_number = "HD-01"
        contract.template_id = uuid4()
        contract.content = "old"
        contract.file_path = "/files/old.pdf"
        contract.status = "active"
        contract_repo.get_by_id.return_value = contract
        contract_repo.update.return_value = contract
        new_contract = AsyncMock(spec=Contract)
        contract_repo.create.return_value = new_contract

        result = await service.renew(
            contract.id,
            uuid4(),
            new_started_on=date(2026, 2, 1),
            new_ended_on=date(2027, 2, 1),
            new_content="new",
        )

        assert result == new_contract
        contract_repo.update.assert_awaited_once_with(contract.id, {"status": "expired", "ended_on": date(2027, 2, 1)})
        contract_repo.create.assert_awaited_once()
        created = contract_repo.create.call_args[0][0]
        assert created.status == "draft"
        assert created.content == "new"
        event_service.record.assert_awaited()

    async def test_terminate_rejects_terminal_contracts(
        self, service: ContractService, contract_repo: AsyncMock
    ) -> None:
        contract = AsyncMock(spec=Contract)
        contract.id = uuid4()
        contract.employee_id = uuid4()
        contract.status = "terminated"
        contract_repo.get_by_id.return_value = contract

        with pytest.raises(ContractStatusTransitionError):
            await service.terminate(contract.id, uuid4())

    async def test_update_draft_rejects_active_contract(
        self, service: ContractService, contract_repo: AsyncMock
    ) -> None:
        contract = AsyncMock(spec=Contract)
        contract.id = uuid4()
        contract.status = "active"
        contract_repo.get_by_id.return_value = contract

        with pytest.raises(ContractAlreadyActiveError):
            await service.update_draft(contract.id, {"content": "x"})

    async def test_get_by_id_raises_when_missing(
        self, service: ContractService, contract_repo: AsyncMock
    ) -> None:
        contract_repo.get_by_id.return_value = None

        with pytest.raises(ContractNotFoundError):
            await service.get_by_id(uuid4())
