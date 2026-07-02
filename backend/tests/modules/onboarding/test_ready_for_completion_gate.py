"""Tests for the ready-for-completion gate and HR confirm completion flow.

Feature: onboarding, KAN-50: ready-for-completion gate

Verifies that completing the last task moves the process to
``ready_for_completion`` (not ``complete``), that HR confirm is the only path
to ``complete`` + employee activation, and that the API rejects direct
activation bypassing HR confirm.

The tests drive the real :class:`OnboardingService` against in-memory fakes
defined inline (no shared conftest), following the same pattern as the other
onboarding property-test modules.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.modules.employee.domain.entities import Employee
from src.modules.identity.domain.entities import User, UserRole
from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.domain.entities import (
    OnboardingAuditLog,
    OnboardingProcess,
    OnboardingTask,
)
from src.modules.onboarding.domain.enums import (
    CHECKLIST_TEMPLATE,
    OnboardingStatus,
    OnboardingTaskStatus,
)
from src.modules.onboarding.domain.exceptions import (
    OnboardingActivationError,
    OnboardingProcessNotFoundError,
)


# ---------------------------------------------------------------------------
# In-memory fakes (inline)
# ---------------------------------------------------------------------------
class _NoOpSavepoint:
    async def __aenter__(self) -> _NoOpSavepoint:
        return self
    async def __aexit__(self, *args: object) -> bool:
        return False

class FakeSession:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
    async def commit(self) -> None:
        self.commit_count += 1
    async def rollback(self) -> None:
        self.rollback_count += 1
    def begin_nested(self) -> _NoOpSavepoint:
        return _NoOpSavepoint()

class FakeProcessRepo:
    def __init__(self) -> None:
        self.processes: list[OnboardingProcess] = []
    async def create(self, process: OnboardingProcess) -> OnboardingProcess:
        self.processes.append(process)
        return process
    async def get_by_id(self, process_id: UUID) -> OnboardingProcess | None:
        for p in self.processes:
            if p.id == process_id:
                return p
        return None
    async def get_for_update(self, process_id: UUID) -> OnboardingProcess | None:
        return await self.get_by_id(process_id)
    async def set_status(self, process: OnboardingProcess, status: str) -> OnboardingProcess:
        now = datetime.now(UTC)
        process.status = status
        process.updated_at = now
        if status == OnboardingStatus.COMPLETE:
            process.completed_at = now
        return process

class FakeTaskRepo:
    def __init__(self) -> None:
        self.tasks: list[OnboardingTask] = []
    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        self.tasks.extend(tasks)
        return tasks
    async def get_by_id(self, task_id: UUID) -> OnboardingTask | None:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    async def set_status(
        self,
        task: OnboardingTask,
        status: OnboardingTaskStatus,
        completed_at: datetime | None = None,
        completed_by_user_id: UUID | None = None,
    ) -> OnboardingTask:
        task.status = status.value
        task.completed_at = completed_at
        task.completed_by_user_id = completed_by_user_id
        return task
    async def list_by_process(self, process_id: UUID) -> list[OnboardingTask]:
        return sorted(
            (t for t in self.tasks if t.process_id == process_id),
            key=lambda t: t.order_index,
        )
    async def count_by_status(self, process_id: UUID) -> dict[str, int]:
        counts: dict[str, int] = {}
        for task in self.tasks:
            if task.process_id == process_id:
                counts[task.status] = counts.get(task.status, 0) + 1
        return counts

class FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list[OnboardingAuditLog] = []
    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        self.entries.append(entry)
        return entry

class FakeEmployeeRepo:
    def __init__(self) -> None:
        self.employees: list[Employee] = []
    async def get_by_id(self, employee_id: UUID) -> Employee | None:
        for e in self.employees:
            if e.id == employee_id:
                return e
        return None
    async def update(self, employee_id: UUID, data: dict) -> Employee | None:
        for e in self.employees:
            if e.id == employee_id:
                for key, val in data.items():
                    setattr(e, key, val)
                return e
        return None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _admin_actor() -> User:
    return User(
        email="hr@example.com",
        name="HR Admin",
        google_sub=f"sub-{uuid4()}",
        role=UserRole.ADMIN,
    )

def _make_employee(
    repo: FakeEmployeeRepo,
    *,
    setup_complete: bool = False,
) -> Employee:
    emp = Employee(
        employee_code="NV-001",
        full_name="Test Employee",
        email="test@example.com",
        candidate_id=uuid4(),
        is_active=False,
    )
    if setup_complete:
        emp.department_id = uuid4()
        emp.position_id = uuid4()
        emp.manager_id = uuid4()
        emp.start_date = datetime.now(UTC).date()
    repo.employees.append(emp)
    return emp

def _make_tasks(
    process_id: UUID,
    done_count: int = 0,
    total: int = 4,
) -> list[OnboardingTask]:
    tasks: list[OnboardingTask] = []
    for i in range(total):
        status = OnboardingTaskStatus.DONE.value if i < done_count else OnboardingTaskStatus.PENDING.value
        template_idx = i % len(CHECKLIST_TEMPLATE)
        _, task_key, name = CHECKLIST_TEMPLATE[template_idx]
        tasks.append(OnboardingTask(
            process_id=process_id,
            task_key=task_key.value,
            name=name,
            status=status,
            order_index=i,
            completed_at=datetime.now(UTC) if status == OnboardingTaskStatus.DONE.value else None,
        ))
    return tasks

def _build_service(
    process_repo: FakeProcessRepo,
    task_repo: FakeTaskRepo,
    audit_repo: FakeAuditRepo,
    employee_repo: FakeEmployeeRepo,
    session: FakeSession,
) -> OnboardingService:
    return OnboardingService(
        process_repo=process_repo,  # type: ignore[arg-type]
        task_repo=task_repo,  # type: ignore[arg-type]
        audit_repo=audit_repo,  # type: ignore[arg-type]
        employee_repo=employee_repo,  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
    )

# ---------------------------------------------------------------------------
# Test: last task done → ready_for_completion (not complete)
# ---------------------------------------------------------------------------
async def _run_last_task_to_ready(
    start_done: int,
    total_tasks: int,
    setup_complete: bool,
) -> tuple[OnboardingProcess, OnboardingService, FakeTaskRepo, FakeAuditRepo, FakeSession, FakeEmployeeRepo]:
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    audit_repo = FakeAuditRepo()
    employee_repo = FakeEmployeeRepo()
    session = FakeSession()

    employee = _make_employee(employee_repo, setup_complete=setup_complete)

    process = OnboardingProcess(
        candidate_id=uuid4(),
        employee_id=employee.id,
        status=OnboardingStatus.IN_PROGRESS.value,
    )
    await process_repo.create(process)

    tasks = _make_tasks(process.id, done_count=start_done, total=total_tasks)
    await task_repo.create_many(tasks)

    service = _build_service(process_repo, task_repo, audit_repo, employee_repo, session)
    actor = _admin_actor()

    # Mark the next pending task done
    pending_tasks = [t for t in tasks if t.status == OnboardingTaskStatus.PENDING.value]
    if pending_tasks:
        await service.complete_task(pending_tasks[0].id, actor)

    return process, service, task_repo, audit_repo, session, employee_repo

def test_last_task_done_makes_process_ready_not_complete() -> None:
    """Last pending task done → process becomes ready_for_completion.

    Employee stays inactive. Process does NOT become complete.
    """
    process, service, task_repo, audit_repo, session, emp_repo = asyncio.run(
        _run_last_task_to_ready(start_done=3, total_tasks=4, setup_complete=True)
    )

    assert process.status == OnboardingStatus.READY_FOR_COMPLETION.value
    assert process.completed_at is None

    # Employee is still inactive
    employee = asyncio.run(emp_repo.get_by_id(process.employee_id))
    assert employee is not None
    assert employee.is_active is False

    # Audit: task_completed + ready_for_completion
    op_types = [e.operation_type for e in audit_repo.entries]
    assert "task_completed" in op_types
    assert "ready_for_completion" in op_types

def test_last_task_done_without_setup_stays_in_progress() -> None:
    """Last task done but setup incomplete → process stays in_progress."""
    process, service, task_repo, audit_repo, session, emp_repo = asyncio.run(
        _run_last_task_to_ready(start_done=3, total_tasks=4, setup_complete=False)
    )

    assert process.status == OnboardingStatus.IN_PROGRESS.value

    op_types = [e.operation_type for e in audit_repo.entries]
    assert "task_completed" in op_types
    assert "ready_for_completion" not in op_types

# ---------------------------------------------------------------------------
# Test: confirm completion from ready_for_completion
# ---------------------------------------------------------------------------
async def _run_confirm_completion() -> tuple[OnboardingProcess, FakeAuditRepo, FakeSession, FakeEmployeeRepo]:
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    audit_repo = FakeAuditRepo()
    employee_repo = FakeEmployeeRepo()
    session = FakeSession()

    employee = _make_employee(employee_repo, setup_complete=True)

    process = OnboardingProcess(
        candidate_id=uuid4(),
        employee_id=employee.id,
        status=OnboardingStatus.READY_FOR_COMPLETION.value,
    )
    await process_repo.create(process)

    tasks = _make_tasks(process.id, done_count=4, total=4)
    await task_repo.create_many(tasks)

    service = _build_service(process_repo, task_repo, audit_repo, employee_repo, session)
    actor = _admin_actor()

    await service.confirm_completion(process.id, actor)
    return process, audit_repo, session, employee_repo

def test_confirm_completion_activates_employee() -> None:
    """HR confirm from ready_for_completion → complete + employee active."""
    process, audit_repo, session, emp_repo = asyncio.run(_run_confirm_completion())

    assert process.status == OnboardingStatus.COMPLETE.value
    assert process.completed_at is not None

    employee = asyncio.run(emp_repo.get_by_id(process.employee_id))
    assert employee is not None
    assert employee.is_active is True

    op_types = [e.operation_type for e in audit_repo.entries]
    assert "confirmed_complete" in op_types
    assert "employee_activated" in op_types

# ---------------------------------------------------------------------------
# Test: confirm completion rejects in_progress
# ---------------------------------------------------------------------------
async def _run_confirm_in_progress_rejected() -> None:
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    audit_repo = FakeAuditRepo()
    employee_repo = FakeEmployeeRepo()
    session = FakeSession()

    employee = _make_employee(employee_repo, setup_complete=True)

    process = OnboardingProcess(
        candidate_id=uuid4(),
        employee_id=employee.id,
        status=OnboardingStatus.IN_PROGRESS.value,
    )
    await process_repo.create(process)

    tasks = _make_tasks(process.id, done_count=4, total=4)
    await task_repo.create_many(tasks)

    service = _build_service(process_repo, task_repo, audit_repo, employee_repo, session)
    actor = _admin_actor()

    await service.confirm_completion(process.id, actor)

def test_confirm_completion_rejects_in_progress() -> None:
    """Calling confirm on in_progress process raises OnboardingActivationError."""
    with pytest.raises(OnboardingActivationError):
        asyncio.run(_run_confirm_in_progress_rejected())

# ---------------------------------------------------------------------------
# Test: confirm completion rejects unknown process
# ---------------------------------------------------------------------------
async def _run_confirm_unknown() -> None:
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    audit_repo = FakeAuditRepo()
    employee_repo = FakeEmployeeRepo()
    session = FakeSession()

    service = _build_service(process_repo, task_repo, audit_repo, employee_repo, session)
    actor = _admin_actor()

    await service.confirm_completion(uuid4(), actor)

def test_confirm_completion_rejects_unknown_process() -> None:
    """Confirm on missing process raises OnboardingProcessNotFoundError."""
    with pytest.raises(OnboardingProcessNotFoundError):
        asyncio.run(_run_confirm_unknown())
