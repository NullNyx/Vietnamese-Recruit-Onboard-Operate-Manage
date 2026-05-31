"""Property-based tests for idempotent onboarding event consumption.

Feature: onboarding, Property 1: Event consumption is idempotent per candidate

This module verifies that delivering the same valid ``candidate_accepted``
event to :meth:`OnboardingService.start_from_event` one or more times is
idempotent per ``candidate_id``: after all deliveries there is exactly one
``OnboardingProcess`` and exactly one ``Employee`` for that candidate, the
process / employee / checklist created by the first delivery are left unchanged
by every subsequent delivery, and each redelivery records exactly one
duplicate-detection audit entry carrying the originating ``candidate_id``.

The test drives the real :class:`OnboardingService` against in-memory fakes so
it executes as a fast, pure-logic check (per the design: "property tests run
against in-memory fakes or mocked repositories"). The fakes are defined inline
in this file to stay self-contained.

Validates: Requirements 1.3, 1.4, 2.7, 3.4
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.onboarding.application.onboarding_service import (
    _OP_DUPLICATE_DETECTED,
    _OP_PROCESS_CREATED,
    OnboardingService,
)
from src.modules.onboarding.domain.entities import (
    OnboardingAuditLog,
    OnboardingProcess,
    OnboardingTask,
)
from src.modules.onboarding.domain.enums import OnboardingTaskStatus

# Printable ASCII excluding the space and '@', used to build valid names and
# email local/domain parts.
_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")


# ---------------------------------------------------------------------------
# In-memory fakes (inline, self-contained)
# ---------------------------------------------------------------------------
class _NoOpSavepoint:
    """Async context manager standing in for ``session.begin_nested()``.

    The service wraps the employee insert in ``async with
    self.session.begin_nested():`` (a SAVEPOINT) to retry on an
    ``employee_code`` collision. The fakes never raise, so this is a pure no-op.
    """

    async def __aenter__(self) -> _NoOpSavepoint:
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False


class FakeSession:
    """Minimal async session: no-op commit/rollback and a no-op SAVEPOINT."""

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
    """In-memory OnboardingProcess store keyed by the idempotency guard."""

    def __init__(self) -> None:
        self.processes: list[OnboardingProcess] = []

    async def get_by_candidate_id(self, candidate_id: UUID) -> OnboardingProcess | None:
        for process in self.processes:
            if process.candidate_id == candidate_id:
                return process
        return None

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


class FakeTaskRepo:
    """In-memory OnboardingTask store."""

    def __init__(self) -> None:
        self.tasks: list[OnboardingTask] = []

    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        self.tasks.extend(tasks)
        return tasks

    async def list_by_process(self, process_id: UUID) -> list[OnboardingTask]:
        return sorted(
            (task for task in self.tasks if task.process_id == process_id),
            key=lambda task: task.order_index,
        )


class FakeAuditRepo:
    """In-memory append-only audit store."""

    def __init__(self) -> None:
        self.entries: list[OnboardingAuditLog] = []

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        self.entries.append(entry)
        return entry


class FakeEmployeeRepo:
    """In-memory Employee store with sequential ``NV-XXX`` code generation."""

    def __init__(self) -> None:
        self.employees: list[Employee] = []
        self._counter = 0

    async def get_next_code(self) -> str:
        self._counter += 1
        return f"NV-{self._counter:03d}"

    async def create(self, employee: Employee) -> Employee:
        self.employees.append(employee)
        return employee


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
@st.composite
def _valid_emails(draw: st.DrawFn) -> str:
    """Syntactically valid email: one '@', non-empty local and domain."""
    local = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    domain = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    return f"{local}@{domain}"


_valid_names = st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=255)


# ---------------------------------------------------------------------------
# Async driver
# ---------------------------------------------------------------------------
async def _run_idempotency_property(
    candidate_id: UUID,
    full_name: str,
    email: str,
    delivery_count: int,
) -> None:
    """Deliver one valid event ``delivery_count`` times and assert idempotence."""
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    audit_repo = FakeAuditRepo()
    employee_repo = FakeEmployeeRepo()
    session = FakeSession()
    service = OnboardingService(
        process_repo=process_repo,  # type: ignore[arg-type]
        task_repo=task_repo,  # type: ignore[arg-type]
        audit_repo=audit_repo,  # type: ignore[arg-type]
        employee_repo=employee_repo,  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
    )

    returned_ids: list[UUID] = []
    snapshot_after_first: dict[str, object] = {}

    for index in range(delivery_count):
        process = await service.start_from_event(
            candidate_id=candidate_id,
            full_name=full_name,
            email=email,
            event_id=f"evt-{index}",
        )
        returned_ids.append(process.id)

        if index == 0:
            # Capture the state established by the very first delivery so later
            # deliveries can be proven to leave it unchanged.
            first_tasks = await task_repo.list_by_process(process.id)
            snapshot_after_first = {
                "process_id": process.id,
                "process_status": process.status,
                "employee_id": process_repo.processes[0].employee_id,
                "task_ids": frozenset(task.id for task in first_tasks),
                "task_statuses": tuple(task.status for task in first_tasks),
            }

    # 1. Exactly one process and exactly one employee for the candidate_id.
    candidate_processes = [p for p in process_repo.processes if p.candidate_id == candidate_id]
    candidate_employees = [e for e in employee_repo.employees if e.candidate_id == candidate_id]
    assert len(candidate_processes) == 1
    assert len(candidate_employees) == 1
    assert len(process_repo.processes) == 1
    assert len(employee_repo.employees) == 1

    # 2. Every delivery returns the same process, and the process / employee /
    #    checklist created by the first delivery are unchanged afterwards.
    assert set(returned_ids) == {snapshot_after_first["process_id"]}
    final_process = candidate_processes[0]
    assert final_process.id == snapshot_after_first["process_id"]
    assert final_process.status == snapshot_after_first["process_status"]
    assert final_process.employee_id == snapshot_after_first["employee_id"]

    final_tasks = await task_repo.list_by_process(final_process.id)
    assert len(final_tasks) == 4
    assert frozenset(task.id for task in final_tasks) == snapshot_after_first["task_ids"]
    assert tuple(task.status for task in final_tasks) == snapshot_after_first["task_statuses"]
    assert all(task.status == OnboardingTaskStatus.PENDING.value for task in final_tasks)

    # 3. Exactly one creation audit and exactly (N - 1) duplicate-detection
    #    audit entries, each duplicate entry carrying the candidate_id.
    creation_entries = [e for e in audit_repo.entries if e.operation_type == _OP_PROCESS_CREATED]
    duplicate_entries = [
        e for e in audit_repo.entries if e.operation_type == _OP_DUPLICATE_DETECTED
    ]
    assert len(creation_entries) == 1
    assert len(duplicate_entries) == delivery_count - 1
    assert all(entry.candidate_id == candidate_id for entry in duplicate_entries)


# Feature: onboarding, Property 1: Event consumption is idempotent per candidate
@settings(max_examples=150, deadline=None)
@given(
    candidate_id=st.uuids(),
    full_name=_valid_names,
    email=_valid_emails(),
    delivery_count=st.integers(min_value=1, max_value=6),
)
def test_event_consumption_is_idempotent_per_candidate(
    candidate_id: UUID,
    full_name: str,
    email: str,
    delivery_count: int,
) -> None:
    """Redelivering a valid event creates one process/employee and audits dupes.

    Validates: Requirements 1.3, 1.4, 2.7, 3.4
    """
    asyncio.run(_run_idempotency_property(candidate_id, full_name, email, delivery_count))
