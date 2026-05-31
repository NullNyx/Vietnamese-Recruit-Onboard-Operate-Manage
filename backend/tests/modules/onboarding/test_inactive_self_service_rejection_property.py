"""Property-based test that self-service access to an inactive employee is rejected.

Feature: onboarding, Property 19: Self-service access to an inactive employee is
rejected

This module drives ``ActiveEmployeeQuery.get_active_by_id`` for any inactive
Employee (``is_active = False``) and asserts the active-Employee boundary guard
rejects the self-service request with an access error
(:class:`InactiveEmployeeAccessError`) while leaving the targeted Employee record
unchanged — the guard performs no writes (R7.2).

The guard wraps the reused ``EmployeeRepository`` (the Employee-query layer). The
fake repository defined inline in this module returns the stored Employee from
``get_by_id`` without ever mutating it (no shared conftest / fakes module, to
avoid collisions with the other onboarding property-test modules). Each example
snapshots the Employee's identifying fields before the call and asserts they are
identical afterwards, with ``is_active`` still ``False``. The raised error must
reference the targeted Employee through ``employee_id``. A second probe with an
unknown id confirms the guard's not-found branch raises
:class:`EmployeeNotFoundError` rather than the inactive-access error.

Validates: Requirements 7.2
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.employee.domain.exceptions import EmployeeNotFoundError
from src.modules.onboarding.application.active_employee_query import ActiveEmployeeQuery
from src.modules.onboarding.domain.exceptions import InactiveEmployeeAccessError

# Printable ASCII excluding the space and '@' so generated names/emails are
# non-empty and emails carry exactly one '@'.
_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")


# ---------------------------------------------------------------------------
# In-memory fake (inline, module-private — no shared fixtures)
# ---------------------------------------------------------------------------
class FakeEmployeeRepo:
    """Read-only Employee-query layer that never mutates the stored Employee.

    ``get_by_id`` returns the pre-seeded Employee when the id matches and
    ``None`` otherwise. The guard is read-only, so this fake exposes no mutating
    methods; if the guard ever attempted a write the test would surface it as an
    ``AttributeError``.
    """

    def __init__(self, employee: Employee) -> None:
        self._employee = employee

    async def get_by_id(self, employee_id: UUID) -> Employee | None:
        if employee_id == self._employee.id:
            return self._employee
        return None


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
def _non_empty_text(max_size: int) -> st.SearchStrategy[str]:
    """Non-empty printable ASCII text without spaces or ``@``."""
    return st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=max_size)


@st.composite
def _emails(draw: st.DrawFn) -> str:
    """Syntactically valid emails: one '@', non-empty local/domain."""
    local = draw(_non_empty_text(64))
    domain = draw(_non_empty_text(64))
    return f"{local}@{domain}"


@st.composite
def _inactive_employees(draw: st.DrawFn) -> Employee:
    """An inactive Employee (``is_active = False``) with varied fields."""
    code_number = draw(st.integers(min_value=0, max_value=999))
    return Employee(
        employee_code=f"NV-{code_number:03d}",
        full_name=draw(_non_empty_text(255)),
        email=draw(_emails()),
        candidate_id=draw(st.uuids()),
        is_active=False,
    )


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------
async def _attempt_access(
    employee: Employee,
) -> tuple[InactiveEmployeeAccessError, bool]:
    """Attempt self-service access to ``employee`` and a probe unknown id.

    Returns the raised :class:`InactiveEmployeeAccessError` and a flag recording
    whether probing an unknown id raised :class:`EmployeeNotFoundError`.
    """
    repo = FakeEmployeeRepo(employee)
    query = ActiveEmployeeQuery(repo)  # type: ignore[arg-type]

    with pytest.raises(InactiveEmployeeAccessError) as exc_info:
        await query.get_active_by_id(employee.id)

    # An unknown id must take the not-found branch, not the inactive branch.
    unknown_id = uuid4()
    not_found_raised = False
    try:
        await query.get_active_by_id(unknown_id)
    except EmployeeNotFoundError:
        not_found_raised = True

    return exc_info.value, not_found_raised


# Feature: onboarding, Property 19: Self-service access to an inactive employee
# is rejected
@settings(max_examples=200, deadline=None)
@given(employee=_inactive_employees())
def test_self_service_access_to_inactive_employee_is_rejected(employee: Employee) -> None:
    """An inactive Employee is rejected with an access error and left unchanged.

    Validates: Requirements 7.2
    """
    # Precondition: the generated Employee is genuinely inactive.
    assert employee.is_active is False

    # Snapshot the identifying fields before the guarded access attempt.
    snapshot = (
        employee.id,
        employee.is_active,
        employee.full_name,
        employee.email,
        employee.employee_code,
        employee.candidate_id,
    )

    error, not_found_raised = asyncio.run(_attempt_access(employee))

    # The access error references the targeted Employee (R7.2).
    assert error.employee_id == employee.id

    # The record is left unchanged by the rejected access — the guard performs
    # no writes; in particular it is still inactive.
    assert employee.is_active is False
    assert (
        employee.id,
        employee.is_active,
        employee.full_name,
        employee.email,
        employee.employee_code,
        employee.candidate_id,
    ) == snapshot

    # The guard's not-found branch is distinct from the inactive-access branch.
    assert not_found_raised is True
