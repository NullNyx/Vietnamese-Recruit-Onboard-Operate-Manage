"""Property-based test for the well-formed initial onboarding state.

Feature: onboarding, Property 2: A new process is created in a well-formed
initial state

This test drives ``OnboardingService.start_from_event`` for any valid
``candidate_accepted`` event and asserts the created state is well-formed:
exactly one ``OnboardingProcess`` (``in_progress``, matching ``candidate_id``),
exactly one linked inactive ``Employee`` (``is_active = False`` with matching
``candidate_id`` / ``full_name`` / ``email`` within the 1-255 / 1-320 bounds),
and exactly four ``pending`` tasks whose names and order match the canonical
``CHECKLIST_TEMPLATE`` (Sign Contract, Submit Documents, Assign Department
Position Manager, Set Start Date).

The checks are fast, pure-logic checks against in-memory fakes defined inline in
this module (no shared conftest / fakes module, to avoid collisions with the
other onboarding property-test modules). The fakes support the transaction
hooks the service uses: ``session.commit()`` / ``session.rollback()`` and the
``session.begin_nested()`` async-context-manager SAVEPOINT used while creating
the employee.

Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
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

# Employee field bounds restated from the requirements (R2.2): full_name is
# 1-255 characters and email is 1-320 characters.
_FULL_NAME_MAX_LENGTH = 255
_EMAIL_MAX_LENGTH = 320

# Printable ASCII excluding the space and '@' so generated names/emails are
# non-empty after trimming and emails carry exactly one '@'.
_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")


# ---------------------------------------------------------------------------
# In-memory fakes (inline, module-private — no shared fixtures)
# ---------------------------------------------------------------------------
class _FakeNestedTransaction:
    """No-op async context manager standing in for a SAVEPOINT.

    Mirrors the object returned by ``AsyncSession.begin_nested()``: it is an
    async context manager, so the service's ``async with
    self.session.begin_nested():`` block enters and exits cleanly without any
    real database savepoint.
    """

    async def __aenter__(self) -> _FakeNestedTransaction:
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


class FakeSession:
    """Minimal async session: no-op commit/rollback and nested transactions.

    Records how many times ``commit`` / ``rollback`` were called so the test can
    confirm the creation path committed exactly once. ``begin_nested`` returns a
    no-op async context manager matching the SAVEPOINT contract the service
    relies on during employee creation.
    """

    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1

    def begin_nested(self) -> _FakeNestedTransaction:
        return _FakeNestedTransaction()


class FakeProcessRepo:
    """Stores created processes in a list; supports the idempotency lookup."""

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


class FakeTaskRepo:
    """Stores created tasks; lists a process's tasks in checklist order."""

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
    """Append-only audit sink collecting entries in a list."""

    def __init__(self) -> None:
        self.entries: list[OnboardingAuditLog] = []

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        self.entries.append(entry)
        return entry


class FakeEmployeeRepo:
    """Generates sequential ``NV-XXX`` codes and stores created employees."""

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
def _full_names() -> st.SearchStrategy[str]:
    """Full names of 1-255 non-whitespace characters (R2.2 bounds)."""
    return st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=_FULL_NAME_MAX_LENGTH)


@st.composite
def _emails(draw: st.DrawFn) -> str:
    """Syntactically valid emails: one '@', non-empty local/domain, <=320."""
    local = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    domain = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    return f"{local}@{domain}"


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------
async def _start_and_collect(
    candidate_id: UUID,
    full_name: str,
    email: str,
) -> tuple[OnboardingProcess, FakeProcessRepo, FakeTaskRepo, FakeEmployeeRepo, FakeSession]:
    """Run ``start_from_event`` against fresh fakes and return the artefacts."""
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    audit_repo = FakeAuditRepo()
    employee_repo = FakeEmployeeRepo()
    session = FakeSession()
    service = OnboardingService(
        process_repo=process_repo,
        task_repo=task_repo,
        audit_repo=audit_repo,
        employee_repo=employee_repo,
        session=session,  # type: ignore[arg-type]
    )

    process = await service.start_from_event(
        candidate_id=candidate_id,
        full_name=full_name,
        email=email,
        event_id="evt-initial-state",
    )
    return process, process_repo, task_repo, employee_repo, session


# Feature: onboarding, Property 2: A new process is created in a well-formed
# initial state
@settings(max_examples=200, deadline=None)
@given(candidate_id=st.uuids(), full_name=_full_names(), email=_emails())
def test_new_process_is_created_in_a_well_formed_initial_state(
    candidate_id: UUID,
    full_name: str,
    email: str,
) -> None:
    """Starting onboarding yields a well-formed process, employee, and checklist.

    Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2
    """
    # The generators stay within the documented field bounds (R2.2).
    assert 1 <= len(full_name) <= _FULL_NAME_MAX_LENGTH
    assert 1 <= len(email) <= _EMAIL_MAX_LENGTH

    process, process_repo, task_repo, employee_repo, session = asyncio.run(
        _start_and_collect(candidate_id, full_name, email)
    )

    # Exactly one OnboardingProcess, in_progress, linked to the event candidate.
    assert len(process_repo.processes) == 1
    assert process is process_repo.processes[0]
    assert process.status == OnboardingStatus.IN_PROGRESS.value
    assert process.candidate_id == candidate_id

    # Exactly one linked inactive Employee with the event's identifying fields.
    assert len(employee_repo.employees) == 1
    employee = employee_repo.employees[0]
    assert employee.is_active is False
    assert employee.candidate_id == candidate_id
    assert employee.full_name == full_name
    assert employee.email == email
    assert process.employee_id == employee.id

    # Exactly four pending tasks whose names and order match the template.
    tasks = asyncio.run(task_repo.list_by_process(process.id))
    assert len(tasks) == 4
    assert all(task.status == OnboardingTaskStatus.PENDING.value for task in tasks)
    assert all(task.process_id == process.id for task in tasks)

    for task, (order_index, task_key, name) in zip(tasks, CHECKLIST_TEMPLATE, strict=True):
        assert task.order_index == order_index
        assert task.task_key == task_key.value
        assert task.name == name

    # The new-candidate creation path committed exactly once and never rolled back.
    assert session.commit_count == 1
    assert session.rollback_count == 0
