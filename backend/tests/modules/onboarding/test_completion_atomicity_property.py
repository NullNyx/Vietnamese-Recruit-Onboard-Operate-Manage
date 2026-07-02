"""Property-based test for atomic task completion (ready_for_completion gate).

Feature: onboarding, KAN-50: ready-for-completion gate — atomicity

Verifies that ``OnboardingService.complete_task`` applies the task status change
and the readiness transition (when all tasks are done) as a single all-or-nothing
transaction together with their mandatory audit writes. If a failure is injected
at *any* step, the whole transaction rolls back so the target task's status and
the process status are left exactly as they were before the call.

Atomicity of ``confirm_completion`` (employee activation) is tested separately
in ``test_confirm_completion_atomicity_property.py``.

Validates: Requirements 5.6, 8.2 (adapted for ready_for_completion gate)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.identity.domain.entities import User, UserRole
from src.modules.onboarding.application.onboarding_service import (
    _OP_READY_FOR_COMPLETION,
    _OP_TASK_COMPLETED,
    OnboardingService,
)
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
from src.modules.onboarding.domain.exceptions import OnboardingError

# Failure steps reachable during complete_task.
#   * task_set_status      -> FakeTaskRepo.set_status raises
#   * status_audit         -> FakeAuditRepo.append raises on task_completed entry
#   * process_set_status   -> FakeProcessRepo.set_status raises (READY_FOR_COMPLETION)
#   * ready_audit          -> FakeAuditRepo.append raises on ready_for_completion entry
_FAILURE_STEPS = ("task_set_status", "status_audit", "process_set_status", "ready_audit")

# Failure steps that are only reached when completing the task makes all tasks done.
_READINESS_STEPS = frozenset({"process_set_status", "ready_audit"})

_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")

class _InjectedFailure(RuntimeError):
    """Raised by a fake repo to simulate a failure at a specific step."""

class FakeTaskRepo:
    def __init__(self, tasks: list[OnboardingTask], fail_on: str | None) -> None:
        self._tasks = tasks
        self.fail_on = fail_on

    async def get_by_id(self, task_id: UUID) -> OnboardingTask | None:
        for task in self._tasks:
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
        if self.fail_on == "task_set_status":
            raise _InjectedFailure("injected failure at task set_status step")
        task.status = status.value
        task.completed_at = completed_at
        task.completed_by_user_id = completed_by_user_id
        return task

    async def count_by_status(self, process_id: UUID) -> dict[str, int]:
        counts: dict[str, int] = {}
        for task in self._tasks:
            if task.process_id == process_id:
                counts[task.status] = counts.get(task.status, 0) + 1
        return counts

class FakeProcessRepo:
    def __init__(self, process: OnboardingProcess, fail_on: str | None) -> None:
        self._process = process
        self.fail_on = fail_on

    async def get_for_update(self, process_id: UUID) -> OnboardingProcess | None:
        if self._process.id == process_id:
            return self._process
        return None

    async def set_status(self, process: OnboardingProcess, status: str) -> OnboardingProcess:
        if self.fail_on == "process_set_status":
            raise _InjectedFailure("injected failure at process set_status step")
        now = datetime.now(UTC)
        process.status = status
        process.updated_at = now
        return process

class FakeEmployeeRepo:
    def __init__(self, employee: Employee) -> None:
        self.employees: list[Employee] = [employee]

    async def get_by_id(self, employee_id: UUID) -> Employee | None:
        for e in self.employees:
            if e.id == employee_id:
                return e
        return None

class FakeAuditRepo:
    def __init__(self, fail_on: str | None) -> None:
        self.fail_on = fail_on
        self.entries: list[OnboardingAuditLog] = []

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        if self.fail_on == "status_audit" and entry.operation_type == _OP_TASK_COMPLETED:
            raise _InjectedFailure("injected failure at status-change audit step")
        if self.fail_on == "ready_audit" and entry.operation_type == _OP_READY_FOR_COMPLETION:
            raise _InjectedFailure("injected failure at readiness audit step")
        self.entries.append(entry)
        return entry

class FakeSession:
    def __init__(
        self,
        tasks: list[OnboardingTask],
        process: OnboardingProcess,
        audit_repo: FakeAuditRepo,
    ) -> None:
        self._tasks = tasks
        self._process = process
        self._audit_repo = audit_repo
        self.commit_count = 0
        self.rollback_count = 0
        self._task_snapshot: dict[UUID, tuple[str, datetime | None, UUID | None]] = {
            task.id: (task.status, task.completed_at, task.completed_by_user_id) for task in tasks
        }
        self._process_status = process.status
        self._process_updated_at = process.updated_at
        self._audit_len = len(audit_repo.entries)

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1
        for task in self._tasks:
            status, completed_at, completed_by = self._task_snapshot[task.id]
            task.status = status
            task.completed_at = completed_at
            task.completed_by_user_id = completed_by
        self._process.status = self._process_status
        self._process.updated_at = self._process_updated_at
        del self._audit_repo.entries[self._audit_len :]

def _build_world(
    fail_on: str | None,
    task_count: int,
    triggers_readiness: bool,
    candidate_id: UUID,
    actor_email: str,
) -> tuple[
    OnboardingService,
    list[OnboardingTask],
    OnboardingTask,
    OnboardingProcess,
    Employee,
    User,
    FakeAuditRepo,
    FakeSession,
]:
    from datetime import date
    from uuid import uuid4
    manager = Employee(
        employee_code="MGR-001",
        full_name="Manager",
        email="manager@example.com",
        is_active=True,
    )
    employee = Employee(
        employee_code="NV-001",
        full_name="Test Employee",
        email="employee@example.com",
        candidate_id=candidate_id,
        is_active=False,
        department_id=uuid4(),
        position_id=uuid4(),
        manager_id=manager.id,
        start_date=date(2026, 1, 1),
    )
    process = OnboardingProcess(
        candidate_id=candidate_id,
        employee_id=employee.id,
        status=OnboardingStatus.IN_PROGRESS.value,
    )
    tasks = [
        OnboardingTask(
            process_id=process.id,
            task_key=task_key.value,
            name=name,
            status=OnboardingTaskStatus.PENDING.value,
            order_index=order_index,
        )
        for order_index, task_key, name in CHECKLIST_TEMPLATE[:task_count]
    ]
    if triggers_readiness:
        for task in tasks[1:]:
            task.status = OnboardingTaskStatus.DONE.value
    else:
        for task in tasks[2:]:
            task.status = OnboardingTaskStatus.DONE.value

    actor = User(
        email=actor_email,
        name="HR Admin",
        google_sub=f"sub-{actor_email}",
        role=UserRole.ADMIN,
    )
    audit_repo = FakeAuditRepo(fail_on)
    session = FakeSession(tasks, process, audit_repo)
    employee_repo = FakeEmployeeRepo(employee)
    employee_repo.employees.append(manager)
    service = OnboardingService(
        process_repo=FakeProcessRepo(process, fail_on),  # type: ignore[arg-type]
        task_repo=FakeTaskRepo(tasks, fail_on),  # type: ignore[arg-type]
        audit_repo=audit_repo,  # type: ignore[arg-type]
        employee_repo=employee_repo,  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
    )
    return service, tasks, tasks[0], process, employee, actor, audit_repo, session

@st.composite
def _scenarios(draw: st.DrawFn) -> tuple[str, int, bool]:
    """Generate (fail_on, task_count, triggers_readiness) scenarios."""
    fail_on = draw(st.sampled_from(_FAILURE_STEPS))
    task_count = draw(st.integers(min_value=1, max_value=4))
    if fail_on in _READINESS_STEPS or task_count == 1:
        triggers_readiness = True
    else:
        triggers_readiness = draw(st.booleans())
    return fail_on, task_count, triggers_readiness

async def _run_atomicity_case(
    fail_on: str,
    task_count: int,
    triggers_readiness: bool,
    candidate_id: UUID,
    actor_email: str,
) -> None:
    (service, tasks, target_task, process, employee, actor, audit_repo, session) = (
        _build_world(fail_on, task_count, triggers_readiness, candidate_id, actor_email)
    )

    pre_task_statuses = {task.id: task.status for task in tasks}
    pre_process_status = process.status
    pre_audit_len = len(audit_repo.entries)

    with pytest.raises(OnboardingError):
        await service.complete_task(target_task.id, actor, status="done")

    assert {task.id: task.status for task in tasks} == pre_task_statuses
    assert process.status == pre_process_status
    assert len(audit_repo.entries) == pre_audit_len
    assert session.rollback_count == 1
    assert session.commit_count == 0

@settings(max_examples=200, deadline=None)
@given(
    scenario=_scenarios(),
    candidate_id=st.uuids(),
    actor_email=st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=24),
)
def test_completion_and_activation_are_atomic_under_injected_failure(
    scenario: tuple[str, int, bool],
    candidate_id: UUID,
    actor_email: str,
) -> None:
    """Any injected failure rolls back task/process/audit state."""
    fail_on, task_count, triggers_readiness = scenario
    asyncio.run(
        _run_atomicity_case(fail_on, task_count, triggers_readiness, candidate_id, actor_email)
    )

async def _run_positive_control_case(candidate_id: UUID, actor_email: str) -> None:
    (service, _tasks, target_task, process, employee, actor, audit_repo, session) = (
        _build_world(
            fail_on=None,
            task_count=2,
            triggers_readiness=True,
            candidate_id=candidate_id,
            actor_email=actor_email,
        )
    )

    # Complete the last pending task (tasks[0] is pending, tasks[1] is already done)
    result = await service.complete_task(target_task.id, actor, status="done")

    # Task is done
    assert result.status == OnboardingTaskStatus.DONE.value
    assert target_task.status == OnboardingTaskStatus.DONE.value

    # Process is ready_for_completion (not complete)
    assert process.status == OnboardingStatus.READY_FOR_COMPLETION.value

    # Employee is still inactive
    assert employee.is_active is False

    # Exactly one task-completed audit and one readiness audit
    op_types = [entry.operation_type for entry in audit_repo.entries]
    assert op_types.count(_OP_TASK_COMPLETED) == 1
    assert op_types.count(_OP_READY_FOR_COMPLETION) == 1
    assert len(audit_repo.entries) == 2

    # The transaction committed exactly once and never rolled back
    assert session.commit_count == 1
    assert session.rollback_count == 0

@settings(max_examples=100, deadline=None)
@given(
    candidate_id=st.uuids(),
    actor_email=st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=24),
)
def test_completion_and_activation_commit_cleanly_without_failure(
    candidate_id: UUID,
    actor_email: str,
) -> None:
    """Positive control: commit path completes task and transitions to ready."""
    asyncio.run(_run_positive_control_case(candidate_id, actor_email))
