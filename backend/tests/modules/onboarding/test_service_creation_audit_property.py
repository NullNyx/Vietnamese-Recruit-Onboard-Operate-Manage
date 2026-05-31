"""Property-based test for the onboarding creation audit entry.

Feature: onboarding, Property 4: A creation audit entry is always written

For any valid ``candidate_accepted`` event that starts a NEW onboarding
process, ``OnboardingService.start_from_event`` must append exactly one
creation audit entry that identifies the originating event id, the created
``OnboardingProcess`` id, the created ``Employee`` id, and the originating
``candidate_id``.

The test drives the real :class:`OnboardingService` against in-memory fakes for
its repositories and session (declared inline in this file to avoid colliding
with sibling property-test agents). The service is async, so each Hypothesis
example is executed via ``asyncio.run`` inside a synchronous ``@given`` test —
the same pattern recommended for combining Hypothesis with async code.

Validates: Requirements 2.8, 8.3
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

# Operation type written by the creation flow for the creation audit entry.
_OP_PROCESS_CREATED = "process_created"

# Printable ASCII excluding the space and '@', used for well-formed field values.
_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")


# --------------------------------------------------------------------------- #
# In-memory fakes (inline, unique to this file)                               #
# --------------------------------------------------------------------------- #
class _FakeSavepoint:
    """Async context manager standing in for an AsyncSession SAVEPOINT."""

    async def __aenter__(self) -> _FakeSavepoint:
        return self

    async def __aexit__(self, *_exc: object) -> bool:
        return False


class FakeSession:
    """Minimal async session: commit/rollback no-ops and a nested SAVEPOINT."""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    def begin_nested(self) -> _FakeSavepoint:
        return _FakeSavepoint()


class FakeProcessRepo:
    """Stores created processes; reports no existing process per candidate."""

    def __init__(self) -> None:
        self.processes: list[OnboardingProcess] = []
        self._by_candidate: dict[UUID, OnboardingProcess] = {}

    async def get_by_candidate_id(self, candidate_id: UUID) -> OnboardingProcess | None:
        return self._by_candidate.get(candidate_id)

    async def create(self, process: OnboardingProcess) -> OnboardingProcess:
        self.processes.append(process)
        self._by_candidate[process.candidate_id] = process
        return process


class FakeTaskRepo:
    """Stores the checklist tasks created for a process."""

    def __init__(self) -> None:
        self.tasks: list[OnboardingTask] = []

    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        self.tasks.extend(tasks)
        return tasks


class FakeAuditRepo:
    """Append-only audit sink: keeps every entry so the test can inspect them."""

    def __init__(self) -> None:
        self.entries: list[OnboardingAuditLog] = []

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        self.entries.append(entry)
        return entry


class FakeEmployeeRepo:
    """Issues sequential NV-XXX codes and stores created employees."""

    def __init__(self) -> None:
        self.employees: list[Employee] = []
        self._counter = 0

    async def get_next_code(self) -> str:
        self._counter += 1
        return f"NV-{self._counter:03d}"

    async def create(self, employee: Employee) -> Employee:
        self.employees.append(employee)
        return employee


# --------------------------------------------------------------------------- #
# Strategies                                                                  #
# --------------------------------------------------------------------------- #
def _valid_names() -> st.SearchStrategy[str]:
    """Employee full names: 1-255 non-whitespace characters."""
    return st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=255)


@st.composite
def _valid_emails(draw: st.DrawFn) -> str:
    """Syntactically valid emails: one '@', non-empty local and domain (<=320)."""
    local = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    domain = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    return f"{local}@{domain}"


def _valid_event_ids() -> st.SearchStrategy[str]:
    """Originating event identifiers (non-empty strings)."""
    return st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64)


async def _start_new_process(
    candidate_id: UUID,
    full_name: str,
    email: str,
    event_id: str,
) -> tuple[OnboardingProcess, FakeEmployeeRepo, FakeAuditRepo]:
    """Run start_from_event against fresh fakes and return the inspect points."""
    process_repo = FakeProcessRepo()
    task_repo = FakeTaskRepo()
    audit_repo = FakeAuditRepo()
    employee_repo = FakeEmployeeRepo()
    session = FakeSession()
    service = OnboardingService(process_repo, task_repo, audit_repo, employee_repo, session)

    process = await service.start_from_event(candidate_id, full_name, email, event_id)
    return process, employee_repo, audit_repo


# Feature: onboarding, Property 4: A creation audit entry is always written
@settings(max_examples=150)
@given(
    candidate_id=st.uuids(),
    full_name=_valid_names(),
    email=_valid_emails(),
    event_id=_valid_event_ids(),
)
def test_creation_audit_entry_is_always_written(
    candidate_id: UUID,
    full_name: str,
    email: str,
    event_id: str,
) -> None:
    """A new process always yields exactly one fully-identifying creation audit.

    Validates: Requirements 2.8, 8.3
    """
    process, employee_repo, audit_repo = asyncio.run(
        _start_new_process(candidate_id, full_name, email, event_id)
    )

    # Exactly one creation audit entry is written for a new process.
    creation_entries = [
        entry for entry in audit_repo.entries if entry.operation_type == _OP_PROCESS_CREATED
    ]
    assert len(creation_entries) == 1
    entry = creation_entries[0]

    # Exactly one employee was created; it is the one linked by the process.
    assert len(employee_repo.employees) == 1
    employee = employee_repo.employees[0]
    assert process.employee_id == employee.id

    # The entry identifies the originating event id.
    assert entry.event_id == event_id

    # The entry identifies the created OnboardingProcess id.
    assert entry.entity_id == process.id
    assert entry.new_value is not None
    assert entry.new_value["process_id"] == str(process.id)

    # The entry identifies the created Employee id.
    assert entry.new_value["employee_id"] == str(employee.id)
    assert entry.new_value["employee_id"] == str(process.employee_id)

    # The entry identifies the originating candidate id.
    assert entry.candidate_id == candidate_id
    assert entry.new_value["candidate_id"] == str(candidate_id)
