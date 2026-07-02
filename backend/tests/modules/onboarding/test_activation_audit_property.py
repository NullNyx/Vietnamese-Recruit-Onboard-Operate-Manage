"""Property-based test: last-task-done transitions to ready_for_completion, not activation.

Feature: onboarding, KAN-50: ready-for-completion gate

Verifies that completing all pending tasks moves the process to
``ready_for_completion`` (not ``complete``), the employee stays inactive, and
no activation audit entry is written. Activation happens only at HR confirm.

The test drives the real :class:`OnboardingService` against in-memory fakes so
it executes as a fast, pure-logic check (per the design: "property tests run
against in-memory fakes or mocked repositories"). The fakes are defined inline
in this file to stay self-contained and avoid collisions with the other
onboarding property-test modules (no shared conftest / fakes module).
"""

from __future__ import annotations

import asyncio
from datetime import date
from uuid import UUID, uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.identity.domain.entities import User, UserRole
from src.modules.onboarding.application.onboarding_service import (
    _OP_EMPLOYEE_ACTIVATED,
    _OP_READY_FOR_COMPLETION,
    OnboardingService,
)
from src.modules.onboarding.domain.entities import (
    OnboardingAuditLog,
    OnboardingProcess,
    OnboardingTask,
)
from src.modules.onboarding.domain.enums import (
    OnboardingStatus,
    OnboardingTaskStatus,
)

# ---------------------------------------------------------------------------
# In-memory fakes (inline, self-contained — no shared fixtures)
# ---------------------------------------------------------------------------
class _NoOpSavepoint:
    async def __aenter__(self) -> _NoOpSavepoint:
        return self
    async def __aexit__(self, *exc_info: object) -> bool:
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
        for process in self.processes:
            if process.id == process_id:
                return process
        return None
    async def get_for_update(self, process_id: UUID) -> OnboardingProcess | None:
        return await self.get_by_id(process_id)
    async def set_status(self, process: OnboardingProcess, status: str) -> OnboardingProcess:
        process.status = status
        return process

class FakeTaskRepo:
    def __init__(self) -> None:
        self.tasks: list[OnboardingTask] = []
    async def get_by_id(self, task_id: UUID) -> OnboardingTask | None:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    async def set_status(
        self,
        task: OnboardingTask,
        status: OnboardingTaskStatus,
        completed_at: object | None = None,
        completed_by_user_id: UUID | None = None,
    ) -> OnboardingTask:
        task.status = status.value
        task.completed_at = completed_at
        task.completed_by_user_id = completed_by_user_id
        return task
    async def count_by_status(self, process_id: UUID) -> dict[str, int]:
        counts: dict[str, int] = {}
        for task in self.tasks:
            if task.process_id == process_id:
                counts[task.status] = counts.get(task.status, 0) + 1
        return counts
    async def list_by_process(self, process_id: UUID) -> list[OnboardingTask]:
        return sorted(
            (task for task in self.tasks if task.process_id == process_id),
            key=lambda task: task.order_index,
        )

class FakeEmployeeRepo:
    def __init__(self) -> None:
        self.employees: list[Employee] = []
    async def create(self, employee: Employee) -> Employee:
        self.employees.append(employee)
        return employee
    async def get_by_id(self, employee_id: UUID) -> Employee | None:
        for employee in self.employees:
            if employee.id == employee_id:
                return employee
        return None
    async def update(self, employee_id: UUID, values: dict[str, object]) -> Employee | None:
        for employee in self.employees:
            if employee.id == employee_id:
                for key, value in values.items():
                    setattr(employee, key, value)
                return employee
        return None

class FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list[OnboardingAuditLog] = []
    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        self.entries.append(entry)
        return entry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_admin_actor() -> User:
    suffix = uuid4().hex
    return User(
        email=f"hr-{suffix}@example.com",
        name="HR Admin",
        google_sub=f"sub-{suffix}",
        role=UserRole.ADMIN,
    )

_Fixture = tuple[
    OnboardingService,
    FakeProcessRepo,
    FakeTaskRepo,
    FakeEmployeeRepo,
    FakeAuditRepo,
    Employee,
    list[UUID],
]

def _build_fixture(task_count: int) -> _Fixture:
    """Set up an in_progress process with ``task_count`` pending tasks.

    Setup fields are pre-filled so the process becomes ready_for_completion
    when the last task is done.
    """
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    employee_repo = FakeEmployeeRepo()
    audit_repo = FakeAuditRepo()
    session = FakeSession()

    candidate_id = uuid4()
    manager = Employee(
        employee_code="MGR-001",
        full_name="Manager",
        email="manager@example.com",
        is_active=True,
    )
    employee_repo.employees.append(manager)

    employee = Employee(
        employee_code="NV-001",
        full_name="New Hire",
        email="new.hire@example.com",
        candidate_id=candidate_id,
        is_active=False,
        department_id=uuid4(),
        position_id=uuid4(),
        manager_id=manager.id,
        start_date=date(2026, 1, 1),
    )
    employee_repo.employees.append(employee)

    process = OnboardingProcess(
        candidate_id=candidate_id,
        employee_id=employee.id,
        status=OnboardingStatus.IN_PROGRESS.value,
    )
    process_repo.processes.append(process)

    task_ids: list[UUID] = []
    for index in range(task_count):
        task = OnboardingTask(
            process_id=process.id,
            task_key=f"task_{index}",
            name=f"Task {index}",
            status=OnboardingTaskStatus.PENDING.value,
            order_index=index,
        )
        task_repo.tasks.append(task)
        task_ids.append(task.id)

    service = OnboardingService(
        process_repo=process_repo,  # type: ignore[arg-type]
        task_repo=task_repo,  # type: ignore[arg-type]
        audit_repo=audit_repo,  # type: ignore[arg-type]
        employee_repo=employee_repo,  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
    )
    return service, process_repo, task_repo, employee_repo, audit_repo, employee, task_ids

async def _complete_all_tasks(task_count: int) -> tuple[FakeProcessRepo, FakeEmployeeRepo, FakeAuditRepo, Employee, User]:
    """Mark every task done and return the artefacts."""
    service, process_repo, _task_repo, employee_repo, audit_repo, employee, task_ids = (
        _build_fixture(task_count)
    )
    actor = _make_admin_actor()
    for task_id in task_ids:
        await service.complete_task(task_id, actor, status=OnboardingTaskStatus.DONE.value)
    return process_repo, employee_repo, audit_repo, employee, actor

# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------
@settings(max_examples=200, deadline=None)
@given(task_count=st.integers(min_value=1, max_value=5))
def test_last_task_done_transitions_to_ready_not_complete(task_count: int) -> None:
    """Completing all pending tasks transitions to ready_for_completion.

    Employee stays inactive. No activation audit entry is written.
    A readiness audit entry is written instead.
    """
    process_repo, employee_repo, audit_repo, employee, actor = asyncio.run(
        _complete_all_tasks(task_count)
    )

    # Process is ready_for_completion, not complete
    assert process_repo.processes[0].status == OnboardingStatus.READY_FOR_COMPLETION.value

    # Employee is still inactive
    assert employee.is_active is False

    # No activation audit entry
    activation_entries = [
        entry for entry in audit_repo.entries if entry.operation_type == _OP_EMPLOYEE_ACTIVATED
    ]
    assert len(activation_entries) == 0

    # Readiness audit entry exists
    readiness_entries = [
        entry for entry in audit_repo.entries if entry.operation_type == _OP_READY_FOR_COMPLETION
    ]
    assert len(readiness_entries) == 1
    readiness = readiness_entries[0]
    assert readiness.user_id == actor.id
    assert readiness.actor_email == actor.email
    assert readiness.entity_type == "process"
