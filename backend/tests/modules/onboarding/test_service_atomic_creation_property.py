"""Property-based test for atomic onboarding-process creation.

Feature: onboarding, Property 6: Creation is atomic

This module verifies that ``OnboardingService.start_from_event`` creates the
inactive Employee, the OnboardingProcess, the four-task checklist, and the
creation audit entry as a single all-or-nothing transaction. If a failure is
injected at *any* creation step (employee, process, tasks, or audit), the
transaction must roll back so that no partial OnboardingProcess and no partial
Employee remain persisted (visible in the committed store).

The repositories and session are replaced with in-memory fakes that model
real commit/rollback semantics with an explicit staging + commit model:

* ``repo.create`` / ``create_many`` / ``append`` stage entities into a *pending*
  buffer; they are NOT visible to ``get_by_candidate_id`` (which reads only the
  *committed* store).
* ``session.commit()`` promotes every pending entity into the committed store.
* ``session.rollback()`` discards the pending buffer entirely.
* ``session.begin_nested()`` provides a SAVEPOINT-like async context manager;
  it lets exceptions propagate, and the outer ``rollback()`` clears all staged
  state, so atomicity holds regardless of which step fails.

A positive control test confirms the commit path works: with no failure
injected, exactly one process and one employee end up in the committed store.

Validates: Requirements 1.5
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.domain.entities import (
    OnboardingAuditLog,
    OnboardingProcess,
    OnboardingTask,
)

# The creation steps, in execution order, at which a failure can be injected.
_CREATION_STEPS = ("employee", "process", "tasks", "audit")

# Printable ASCII excluding the space and '@', used to build valid-looking
# names/emails/event ids that vary the event data.
_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")


@dataclass(frozen=True)
class _Event:
    """A valid ``candidate_accepted`` event payload (already validated)."""

    candidate_id: UUID
    full_name: str
    email: str
    event_id: str


class _InjectedFailure(RuntimeError):
    """Raised by a fake repo to simulate a failure at a specific step."""


class FakeDB:
    """Shared in-memory store with staging + commit/rollback semantics.

    Each entity kind has a *committed* store (visible to reads) and a *pending*
    buffer (staged writes not yet committed). ``commit`` promotes pending into
    committed; ``rollback`` discards the pending buffer. This lets the test
    assert that a rolled-back creation leaves nothing partial in the committed
    store.
    """

    def __init__(self) -> None:
        self.employees_committed: dict[UUID, Employee] = {}
        self.processes_committed: dict[UUID, OnboardingProcess] = {}
        self.tasks_committed: dict[UUID, OnboardingTask] = {}
        self.audits_committed: list[OnboardingAuditLog] = []

        self.employees_pending: dict[UUID, Employee] = {}
        self.processes_pending: dict[UUID, OnboardingProcess] = {}
        self.tasks_pending: dict[UUID, OnboardingTask] = {}
        self.audits_pending: list[OnboardingAuditLog] = []

    def commit(self) -> None:
        """Promote every staged entity into the committed store."""
        self.employees_committed.update(self.employees_pending)
        self.processes_committed.update(self.processes_pending)
        self.tasks_committed.update(self.tasks_pending)
        self.audits_committed.extend(self.audits_pending)
        self._clear_pending()

    def rollback(self) -> None:
        """Discard every staged (uncommitted) entity."""
        self._clear_pending()

    def _clear_pending(self) -> None:
        self.employees_pending.clear()
        self.processes_pending.clear()
        self.tasks_pending.clear()
        self.audits_pending.clear()


class _FakeNested:
    """SAVEPOINT-like async context manager that propagates exceptions."""

    async def __aenter__(self) -> _FakeNested:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        # Never suppress: let any exception propagate so the OUTER rollback
        # clears all staged state (the source of atomicity here).
        return False


class FakeSession:
    """Minimal async session modelling commit/rollback over a shared FakeDB."""

    def __init__(self, db: FakeDB) -> None:
        self.db = db

    async def commit(self) -> None:
        self.db.commit()

    async def rollback(self) -> None:
        self.db.rollback()

    def begin_nested(self) -> _FakeNested:
        return _FakeNested()


class FakeEmployeeRepo:
    """Fake EmployeeRepository: stages employees and hands out NV-XXX codes."""

    def __init__(self, db: FakeDB, fail_on: str | None) -> None:
        self.db = db
        self.fail_on = fail_on
        self._counter = 0

    async def get_next_code(self) -> str:
        self._counter += 1
        return f"NV-{self._counter:03d}"

    async def create(self, employee: Employee) -> Employee:
        if self.fail_on == "employee":
            raise _InjectedFailure("injected failure at employee creation step")
        self.db.employees_pending[employee.id] = employee
        return employee


class FakeProcessRepo:
    """Fake OnboardingProcessRepository with committed-only reads."""

    def __init__(self, db: FakeDB, fail_on: str | None) -> None:
        self.db = db
        self.fail_on = fail_on

    async def get_by_candidate_id(self, candidate_id: UUID) -> OnboardingProcess | None:
        # Idempotency guard reads the COMMITTED store only.
        for process in self.db.processes_committed.values():
            if process.candidate_id == candidate_id:
                return process
        return None

    async def create(self, process: OnboardingProcess) -> OnboardingProcess:
        if self.fail_on == "process":
            raise _InjectedFailure("injected failure at process creation step")
        self.db.processes_pending[process.id] = process
        return process


class FakeTaskRepo:
    """Fake OnboardingTaskRepository staging checklist tasks."""

    def __init__(self, db: FakeDB, fail_on: str | None) -> None:
        self.db = db
        self.fail_on = fail_on

    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        if self.fail_on == "tasks":
            raise _InjectedFailure("injected failure at checklist creation step")
        for task in tasks:
            self.db.tasks_pending[task.id] = task
        return tasks


class FakeAuditRepo:
    """Fake append-only OnboardingAuditRepository."""

    def __init__(self, db: FakeDB, fail_on: str | None) -> None:
        self.db = db
        self.fail_on = fail_on

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        if self.fail_on == "audit":
            raise _InjectedFailure("injected failure at creation-audit step")
        self.db.audits_pending.append(entry)
        return entry


def _build_service(db: FakeDB, fail_on: str | None) -> OnboardingService:
    """Wire an OnboardingService over fakes sharing one FakeDB."""
    session = FakeSession(db)
    return OnboardingService(
        process_repo=FakeProcessRepo(db, fail_on),  # type: ignore[arg-type]
        task_repo=FakeTaskRepo(db, fail_on),  # type: ignore[arg-type]
        audit_repo=FakeAuditRepo(db, fail_on),  # type: ignore[arg-type]
        employee_repo=FakeEmployeeRepo(db, fail_on),  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
    )


@st.composite
def _valid_events(draw: st.DrawFn) -> _Event:
    """Generate varied, valid ``candidate_accepted`` event data."""
    candidate_id = draw(st.uuids())
    full_name = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=255))
    local = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=32))
    domain = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=32))
    event_id = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=40))
    return _Event(candidate_id, full_name, f"{local}@{domain}", event_id)


async def _run_injected_failure_case(event: _Event, failing_step: str) -> None:
    """Inject a failure at one creation step and assert nothing partial persists."""
    db = FakeDB()
    service = _build_service(db, fail_on=failing_step)

    with pytest.raises(_InjectedFailure):
        await service.start_from_event(
            candidate_id=event.candidate_id,
            full_name=event.full_name,
            email=event.email,
            event_id=event.event_id,
        )

    # No partial OnboardingProcess for this candidate remains committed (R1.5).
    assert all(
        process.candidate_id != event.candidate_id for process in db.processes_committed.values()
    )
    # No partial Employee for this candidate remains committed (R1.5).
    assert all(
        employee.candidate_id != event.candidate_id for employee in db.employees_committed.values()
    )
    # Stronger guarantee: the failed transaction committed nothing at all.
    assert db.processes_committed == {}
    assert db.employees_committed == {}
    assert db.tasks_committed == {}
    assert db.audits_committed == []
    # And the staging buffers were cleared by the rollback (no leaked state).
    assert db.employees_pending == {}
    assert db.processes_pending == {}
    assert db.tasks_pending == {}
    assert db.audits_pending == []


# Feature: onboarding, Property 6: Creation is atomic
@settings(max_examples=200, deadline=None)
@given(event=_valid_events(), failing_step=st.sampled_from(_CREATION_STEPS))
def test_creation_is_atomic_under_injected_failure(event: _Event, failing_step: str) -> None:
    """A failure at any creation step rolls back with no partial state.

    Validates: Requirements 1.5
    """
    asyncio.run(_run_injected_failure_case(event, failing_step))


async def _run_positive_control_case(event: _Event) -> None:
    """With no failure injected, the creation transaction commits cleanly."""
    db = FakeDB()
    service = _build_service(db, fail_on=None)

    process = await service.start_from_event(
        candidate_id=event.candidate_id,
        full_name=event.full_name,
        email=event.email,
        event_id=event.event_id,
    )

    # Exactly one process and one employee are present in the committed store.
    assert len(db.processes_committed) == 1
    assert len(db.employees_committed) == 1

    committed_process = next(iter(db.processes_committed.values()))
    assert committed_process.id == process.id
    assert committed_process.candidate_id == event.candidate_id

    committed_employee = next(iter(db.employees_committed.values()))
    assert committed_employee.candidate_id == event.candidate_id
    assert committed_employee.is_active is False

    # The full checklist and the single creation audit entry are committed too.
    assert len(db.tasks_committed) == 4
    assert len(db.audits_committed) == 1
    # Nothing left dangling in the staging buffers after commit.
    assert db.processes_pending == {}
    assert db.employees_pending == {}
    assert db.tasks_pending == {}
    assert db.audits_pending == []


# Feature: onboarding, Property 6: Creation is atomic (positive control)
@settings(max_examples=100, deadline=None)
@given(event=_valid_events())
def test_creation_commits_exactly_one_process_and_employee(event: _Event) -> None:
    """Sanity check that the fakes' commit path persists exactly one of each.

    Validates: Requirements 1.5
    """
    asyncio.run(_run_positive_control_case(event))
