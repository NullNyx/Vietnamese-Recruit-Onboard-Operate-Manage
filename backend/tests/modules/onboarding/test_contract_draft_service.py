from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.modules.identity.domain.entities import User, UserRole
from src.modules.onboarding.application.onboarding_service import OnboardingService


class _Session:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class _ProcessRepo:
    def __init__(self, process):
        self.process = process

    async def get_for_update(self, process_id):
        return self.process if self.process.id == process_id else None

    async def get_by_id(self, process_id):
        return self.process if self.process.id == process_id else None


class _ContractRepo:
    def __init__(self, draft):
        self.draft = draft

    async def get_by_process(self, process_id):
        return self.draft if self.draft.process_id == process_id else None

    async def update(self, draft):
        self.draft = draft
        return draft

    async def create(self, draft):
        self.draft = draft
        return draft


class _EmployeeRepo:
    def __init__(self, employee):
        self.employee = employee

    async def get_by_id(self, employee_id):
        return self.employee if self.employee.id == employee_id else None


class _AuditRepo:
    async def append(self, entry):
        return entry


@pytest.mark.asyncio
async def test_generate_contract_draft_and_advance_status():
    process_id = uuid4()
    candidate_id = uuid4()
    employee_id = uuid4()
    user = User(id=uuid4(), email="hr@example.com", role=UserRole.ADMIN)
    process = SimpleNamespace(
        id=process_id, candidate_id=candidate_id, employee_id=employee_id, status="in_progress"
    )
    employee = SimpleNamespace(id=employee_id, full_name="Nguyen Van A", employee_code="NV-001")
    draft = SimpleNamespace(
        id=uuid4(),
        process_id=process_id,
        contract_type="labor",
        content=None,
        status="draft",
        revision=1,
        created_by=None,
        updated_by=None,
        created_at=SimpleNamespace(isoformat=lambda: "2026-07-02T00:00:00+07:00"),
        updated_at=SimpleNamespace(isoformat=lambda: "2026-07-02T00:00:00+07:00"),
    )

    service = OnboardingService(
        process_repo=_ProcessRepo(process),
        task_repo=SimpleNamespace(),
        audit_repo=_AuditRepo(),
        employee_repo=_EmployeeRepo(employee),
        session=_Session(),
        contract_repo=_ContractRepo(draft),
    )

    generated = await service.generate_contract_draft(process_id, user)
    assert generated.revision == 2
    assert "Nguyen Van A" in (generated.content or "")

    ready = await service.update_contract_status(process_id, user, "ready")
    assert ready.status == "ready"
