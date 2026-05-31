"""Property-based test for employee_code format and uniqueness.

Feature: onboarding, Property 3: Every created employee_code is well-formed and
unique

This test exercises ``OnboardingService.start_from_event`` against a batch of
distinct, valid ``candidate_accepted`` events delivered through one shared
service instance backed by in-memory fakes. For any such sequence, every
``Employee`` the service creates must carry an ``employee_code`` matching the
``NV-XXX`` shape (the literal prefix ``NV-`` followed by exactly three digits),
and across all created employees the set of codes must contain no duplicates.

The fakes model the contract the service relies on: ``FakeEmployeeRepo``
hands out sequentially increasing ``NV-001``, ``NV-002`` ... codes via
``get_next_code`` (mirroring the real repository's MAX-derived generator) and
records every employee it persists so the test can read all codes back. Because
the batch size is capped at 20, the sequence never exceeds ``NV-999`` and stays
within the three-digit form.

Validates: Requirements 2.4
"""

from __future__ import annotations

import asyncio
import re
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

# An ``NV-`` prefix followed by exactly three digits (R2.4).
_EMPLOYEE_CODE_PATTERN = re.compile(r"^NV-\d{3}$")

# Printable ASCII excluding the space and '@', used for well-formed name/email
# field values. Only the produced ``employee_code`` matters to this property,
# but realistic payloads keep the scenario faithful to the consumer contract.
_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")


class FakeProcessRepo:
    """In-memory stand-in for ``OnboardingProcessRepository``.

    ``get_by_candidate_id`` returns ``None`` for candidates not yet seen (so a
    new event creates a fresh process + employee) and the previously stored
    process otherwise; ``create`` records the process for both lookups.
    """

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
    """In-memory stand-in for ``OnboardingTaskRepository``."""

    def __init__(self) -> None:
        self.tasks: list[OnboardingTask] = []

    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        self.tasks.extend(tasks)
        return tasks


class FakeAuditRepo:
    """In-memory append-only stand-in for ``OnboardingAuditRepository``."""

    def __init__(self) -> None:
        self.entries: list[OnboardingAuditLog] = []

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        self.entries.append(entry)
        return entry


class FakeEmployeeRepo:
    """In-memory stand-in for the reused ``EmployeeRepository``.

    ``get_next_code`` returns sequentially increasing ``NV-XXX`` codes
    (``NV-001``, ``NV-002`` ...), honoring both the format and uniqueness of the
    real MAX-derived generator. Every created employee is tracked so the test
    can read back all assigned codes.
    """

    def __init__(self) -> None:
        self._counter = 0
        self.created: list[Employee] = []

    async def get_next_code(self) -> str:
        self._counter += 1
        return f"NV-{self._counter:03d}"

    async def create(self, employee: Employee) -> Employee:
        self.created.append(employee)
        return employee


class _NoOpNestedTransaction:
    """No-op async context manager standing in for a SAVEPOINT."""

    async def __aenter__(self) -> _NoOpNestedTransaction:
        return self

    async def __aexit__(self, *_exc: object) -> bool:
        return False


class FakeSession:
    """Minimal async session: commit/rollback are no-ops; nested is a no-op CM."""

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    def begin_nested(self) -> _NoOpNestedTransaction:
        return _NoOpNestedTransaction()


def _valid_names() -> st.SearchStrategy[str]:
    """Employee full names within the 1-255 character bound."""
    return st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=255)


@st.composite
def _valid_emails(draw: st.DrawFn) -> str:
    """Syntactically valid emails: one '@', non-empty local and domain."""
    local = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    domain = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    return f"{local}@{domain}"


@st.composite
def _event_batches(draw: st.DrawFn) -> list[tuple[UUID, str, str]]:
    """A batch of 1-20 distinct valid events as ``(candidate_id, name, email)``.

    The ``candidate_id`` values are unique so each event creates a new process
    and employee. The batch is capped at 20 so the sequential ``NV-XXX`` codes
    stay within the three-digit range.
    """
    candidate_ids = draw(st.lists(st.uuids(), min_size=1, max_size=20, unique=True))
    n = len(candidate_ids)
    names = draw(st.lists(_valid_names(), min_size=n, max_size=n))
    emails = draw(st.lists(_valid_emails(), min_size=n, max_size=n))
    return list(zip(candidate_ids, names, emails, strict=True))


async def _run_events(events: list[tuple[UUID, str, str]]) -> list[Employee]:
    """Deliver every event through one shared service instance and fakes.

    Returns the list of all employees created across the batch so the caller can
    assert on the assigned ``employee_code`` values.
    """
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

    for index, (candidate_id, full_name, email) in enumerate(events):
        await service.start_from_event(candidate_id, full_name, email, f"evt-{index}")

    return employee_repo.created


# Feature: onboarding, Property 3: Every created employee_code is well-formed and
# unique
@settings(max_examples=200)
@given(events=_event_batches())
def test_employee_codes_are_well_formed_and_unique(
    events: list[tuple[UUID, str, str]],
) -> None:
    """Every created employee_code matches ``^NV-\\d{3}$`` and is unique.

    Validates: Requirements 2.4
    """
    created = asyncio.run(_run_events(events))

    # One employee is created per distinct event.
    assert len(created) == len(events)

    codes = [employee.employee_code for employee in created]

    # Every code is well-formed: literal ``NV-`` then exactly three digits.
    for code in codes:
        assert _EMPLOYEE_CODE_PATTERN.match(code) is not None, code

    # No two created employees share a code.
    assert len(set(codes)) == len(codes)
