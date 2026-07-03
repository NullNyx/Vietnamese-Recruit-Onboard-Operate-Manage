"""Tests for onboarding template management and template-driven generation."""

from __future__ import annotations

import asyncio
from unittest.mock import patch
from uuid import UUID, uuid4

from src.modules.employee.domain.entities import Employee
from src.modules.identity.domain.entities import User, UserRole
from src.modules.onboarding.api.router import list_documents
from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.application.template_service import OnboardingTemplateService
from src.modules.onboarding.domain.entities import (
    OnboardingAuditLog,
    OnboardingContractDraft,
    OnboardingDocument,
    OnboardingProcess,
    OnboardingTask,
    OnboardingTemplate,
)
from src.modules.onboarding.domain.enums import DOCUMENT_TEMPLATE


class FakeSession:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1

    def begin_nested(self):  # noqa: ANN201
        class _Tx:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc: object) -> bool:
                return False

        return _Tx()


class FakeTemplateRepo:
    def __init__(self, templates: list[OnboardingTemplate] | None = None) -> None:
        self.templates = templates or []
        self.created: list[OnboardingTemplate] = []

    async def list(self, template_type: str | None = None, include_archived: bool = False):
        items = self.templates
        if template_type is not None:
            items = [item for item in items if item.template_type == template_type]
        if not include_archived:
            items = [item for item in items if not item.is_archived]
        return sorted(
            items, key=lambda item: (item.template_type, item.order_index, item.display_name)
        )

    async def get_by_id(self, template_id: UUID) -> OnboardingTemplate | None:
        for template in self.templates:
            if template.id == template_id:
                return template
        return None

    async def get_by_key(
        self, template_type: str, key: str, include_archived: bool = False
    ) -> OnboardingTemplate | None:
        for template in self.templates:
            if template.template_type != template_type:
                continue
            if template.key != key:
                continue
            if not include_archived and template.is_archived:
                continue
            return template
        return None

    async def create(self, template: OnboardingTemplate) -> OnboardingTemplate:
        self.templates.append(template)
        self.created.append(template)
        return template

    async def update(self, template: OnboardingTemplate) -> OnboardingTemplate:
        return template


class FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list[OnboardingAuditLog] = []

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        self.entries.append(entry)
        return entry


class FakeProcessRepo:
    def __init__(self) -> None:
        self.processes: list[OnboardingProcess] = []

    async def get_by_candidate_id(self, candidate_id: UUID) -> OnboardingProcess | None:
        return None

    async def create(self, process: OnboardingProcess) -> OnboardingProcess:
        self.processes.append(process)
        return process


class FakeTaskRepo:
    def __init__(self) -> None:
        self.tasks: list[OnboardingTask] = []

    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        self.tasks.extend(tasks)
        return tasks


class FakeDocumentRepo:
    def __init__(self) -> None:
        self.documents: list[OnboardingDocument] = []

    async def create_many(self, docs: list[OnboardingDocument]) -> list[OnboardingDocument]:
        self.documents.extend(docs)
        return docs


class FakeContractRepo:
    def __init__(self) -> None:
        self.contracts: list[OnboardingContractDraft] = []

    async def create(self, draft: OnboardingContractDraft) -> OnboardingContractDraft:
        self.contracts.append(draft)
        return draft


class FakeEmployeeRepo:
    def __init__(self) -> None:
        self.employees: list[Employee] = []

    async def get_next_code(self) -> str:
        return "NV-001"

    async def create(self, employee: Employee) -> Employee:
        self.employees.append(employee)
        return employee


def _admin_user() -> User:
    suffix = uuid4().hex[:8]
    return User(
        email=f"hr-{suffix}@example.com",
        name="HR Admin",
        google_sub=f"sub-{suffix}",
        role=UserRole.ADMIN,
    )


def test_template_crud_is_audited() -> None:
    async def run() -> list[str]:
        session = FakeSession()
        repo = FakeTemplateRepo(
            [
                OnboardingTemplate(
                    id=uuid4(),
                    template_type="task",
                    key="sign_contract",
                    display_name="Sign Contract",
                    description="Seed",
                    order_index=0,
                    is_system=True,
                )
            ]
        )
        audit_repo = FakeAuditRepo()
        service = OnboardingTemplateService(repo, audit_repo, session)  # type: ignore[arg-type]
        actor = _admin_user()

        created = await service.create_template(
            actor,
            {
                "template_type": "contract",
                "key": "labor_contract",
                "display_name": "Labor Contract",
                "description": "Draft",
                "template_body": "Hello {{candidate_name}}",
                "is_required": True,
                "order_index": 0,
                "version": 1,
                "is_system": False,
                "is_archived": False,
            },
        )
        await service.update_template(
            created.id,
            actor,
            {"display_name": "Labor Contract v2", "template_body": "Hi {{candidate_name}}"},
        )
        await service.archive_template(created.id, actor)

        assert session.commit_count == 3
        assert [entry.operation_type for entry in audit_repo.entries] == [
            "template_created",
            "template_updated",
            "template_archived",
        ]
        assert audit_repo.entries[-1].new_value is not None
        assert audit_repo.entries[-1].new_value["is_archived"] is True
        return [template.key for template in repo.templates]

    keys = asyncio.run(run())
    assert "labor_contract" in keys

def test_template_create_rejects_duplicate_key() -> None:
    async def run() -> None:
        session = FakeSession()
        repo = FakeTemplateRepo(
            [
                OnboardingTemplate(
                    id=uuid4(),
                    template_type="document",
                    key="cccd",
                    display_name="CCCD",
                    order_index=0,
                )
            ]
        )
        audit_repo = FakeAuditRepo()
        service = OnboardingTemplateService(repo, audit_repo, session)  # type: ignore[arg-type]
        actor = _admin_user()

        try:
            await service.create_template(
                actor,
                {
                    "template_type": "document",
                    "key": "cccd",
                    "display_name": "CCCD copy",
                    "description": "Dup",
                    "is_required": True,
                    "order_index": 1,
                    "version": 1,
                    "is_system": False,
                    "is_archived": False,
                },
            )
        except Exception as exc:
            assert exc.__class__.__name__ == "HTTPException"
            assert getattr(exc, "status_code") == 409
            assert getattr(exc, "detail") == {"code": "TEMPLATE_DUPLICATE"}
        else:
            raise AssertionError("duplicate template must fail")

        assert session.commit_count == 0
        assert audit_repo.entries == []

    asyncio.run(run())

def test_preview_renders_document_task_and_contract_full_text() -> None:
    async def run() -> tuple[str, str, str]:
        session = FakeSession()
        service = OnboardingTemplateService(FakeTemplateRepo(), FakeAuditRepo(), session)  # type: ignore[arg-type]

        document = OnboardingTemplate(
            id=uuid4(),
            template_type="document",
            key="cccd",
            display_name="CCCD",
            description="Giấy tờ tùy thân",
            order_index=0,
            is_required=True,
        )
        task = OnboardingTemplate(
            id=uuid4(),
            template_type="task",
            key="sign_contract",
            display_name="Sign Contract",
            description="Ký hợp đồng",
            order_index=0,
            is_required=True,
        )
        contract = OnboardingTemplate(
            id=uuid4(),
            template_type="contract",
            key="labor_contract",
            display_name="Labor Contract",
            description="Draft",
            template_body=(
                "Labor Contract\n"
                "Candidate: {{candidate_name}}\n"
                "Employee code: {{employee_code}}\n"
                "Process ID: {{process_id}}\n"
                "Candidate ID: {{candidate_id}}\n"
            ),
            order_index=0,
            is_required=True,
        )

        assert service._render_preview(document) == "[Required] CCCD: Giấy tờ tùy thân"
        assert service._render_preview(task) == "1. Sign Contract — Ký hợp đồng"
        preview = service._render_preview(contract)
        return (
            preview,
            str(document.id),
            str(task.id),
        )

    preview, _, _ = asyncio.run(run())
    assert "Nguyễn Văn A" in preview
    assert "NV-001" in preview
    assert "00000000-0000-0000-0000-000000000000" in preview
    assert "11111111-1111-1111-1111-111111111111" in preview

def test_list_documents_falls_back_to_document_template() -> None:
    class EmptyDocumentRepo:
        def __init__(self, session: object) -> None:
            self.session = session
            self.created: list[object] = []

        async def list_by_process(self, process_id: UUID) -> list[object]:
            return []

        async def create_many(self, docs: list[object]) -> list[object]:
            self.created.extend(docs)
            return docs

    class EmptyTemplateRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        async def list(self, template_type: str | None = None, include_archived: bool = False):
            return []

    async def run() -> list[str]:
        process_id = uuid4()
        document_repo_path = "src.modules.onboarding.api.router.OnboardingDocumentRepository"
        template_repo_path = "src.modules.onboarding.api.router.OnboardingTemplateRepository"
        with (
            patch(document_repo_path, EmptyDocumentRepo),
            patch(template_repo_path, EmptyTemplateRepo),
        ):
            docs = await list_documents(process_id, object(), object())  # type: ignore[arg-type]
        return [doc.display_name for doc in docs]

    assert asyncio.run(run()) == [display_name for _, display_name, _ in DOCUMENT_TEMPLATE]

def test_contract_template_prefers_system_then_lowest_order() -> None:
    async def run() -> tuple[str, str]:
        session = FakeSession()
        repo = FakeTemplateRepo(
            [
                OnboardingTemplate(
                    id=uuid4(),
                    template_type="contract",
                    key="custom_b",
                    display_name="Custom B",
                    order_index=10,
                    is_system=False,
                ),
                OnboardingTemplate(
                    id=uuid4(),
                    template_type="contract",
                    key="system_contract",
                    display_name="System Contract",
                    order_index=9,
                    is_system=True,
                ),
                OnboardingTemplate(
                    id=uuid4(),
                    template_type="contract",
                    key="custom_a",
                    display_name="Custom A",
                    order_index=1,
                    is_system=False,
                ),
            ]
        )
        service = OnboardingService(
            process_repo=FakeProcessRepo(),
            task_repo=FakeTaskRepo(),
            audit_repo=FakeAuditRepo(),
            employee_repo=FakeEmployeeRepo(),
            session=session,  # type: ignore[arg-type]
            document_repo=FakeDocumentRepo(),
            contract_repo=FakeContractRepo(),
            template_repo=repo,  # type: ignore[arg-type]
        )
        chosen = await service._get_contract_template()
        assert chosen is not None
        system_only_repo = FakeTemplateRepo(
            [
                OnboardingTemplate(
                    id=uuid4(),
                    template_type="contract",
                    key="custom_b",
                    display_name="Custom B",
                    order_index=10,
                    is_system=False,
                ),
                OnboardingTemplate(
                    id=uuid4(),
                    template_type="contract",
                    key="custom_a",
                    display_name="Custom A",
                    order_index=1,
                    is_system=False,
                ),
            ]
        )
        fallback_service = OnboardingService(
            process_repo=FakeProcessRepo(),
            task_repo=FakeTaskRepo(),
            audit_repo=FakeAuditRepo(),
            employee_repo=FakeEmployeeRepo(),
            session=session,  # type: ignore[arg-type]
            document_repo=FakeDocumentRepo(),
            contract_repo=FakeContractRepo(),
            template_repo=system_only_repo,  # type: ignore[arg-type]
        )
        fallback = await fallback_service._get_contract_template()
        assert fallback is not None
        return chosen.key, fallback.key

    chosen_key, fallback_key = asyncio.run(run())
    assert chosen_key == "system_contract"
    assert fallback_key == "custom_a"


def test_onboarding_uses_persisted_templates() -> None:
    async def run() -> tuple[list[str], list[str], str]:
        session = FakeSession()
        task_template = OnboardingTemplate(
            id=uuid4(),
            template_type="task",
            key="custom_task",
            display_name="Custom Task",
            description="Task from DB",
            order_index=0,
            is_system=False,
        )
        document_template = OnboardingTemplate(
            id=uuid4(),
            template_type="document",
            key="custom_doc",
            display_name="Custom Document",
            description="Document from DB",
            is_required=False,
            order_index=0,
            is_system=False,
        )
        contract_template = OnboardingTemplate(
            id=uuid4(),
            template_type="contract",
            key="custom_contract",
            display_name="Custom Contract",
            description="Contract from DB",
            template_body="Candidate {{candidate_name}} / Code {{employee_code}}",
            order_index=0,
            is_system=False,
        )
        template_repo = FakeTemplateRepo([task_template, document_template, contract_template])
        service = OnboardingService(
            process_repo=FakeProcessRepo(),
            task_repo=FakeTaskRepo(),
            audit_repo=FakeAuditRepo(),
            employee_repo=FakeEmployeeRepo(),
            session=session,  # type: ignore[arg-type]
            document_repo=FakeDocumentRepo(),
            contract_repo=FakeContractRepo(),
            template_repo=template_repo,  # type: ignore[arg-type]
        )
        process = await service.start_from_event(
            candidate_id=uuid4(),
            full_name="Nguyen Van A",
            email="a@example.com",
            event_id="evt-templates",
        )
        task_names = [task.name for task in service.task_repo.tasks]  # type: ignore[attr-defined]
        document_names = [doc.display_name for doc in service.document_repo.documents]  # type: ignore[attr-defined]
        contract_content = service.contract_repo.contracts[0].content  # type: ignore[attr-defined]
        assert process.status == "in_progress"
        return task_names, document_names, contract_content or ""

    task_names, document_names, contract_content = asyncio.run(run())
    assert task_names == ["Custom Task"]
    assert document_names == ["Custom Document"]
    assert "Nguyen Van A" in contract_content
    assert "NV-001" in contract_content
