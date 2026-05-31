"""Property-based test for the active-Employee boundary inclusion contract.

Feature: onboarding, Property 18: The active-Employee boundary includes exactly
the active employees

This test drives ``ActiveEmployeeQuery.list_active`` over arbitrary populations
of Employee records carrying varied ``is_active`` flags and asserts the boundary
returns *exactly* the active records: every ``is_active = True`` record is
included, no ``is_active = False`` record appears, and the reported ``total``
equals the number of active records (R7.1, R7.3, R7.4).

The check is a fast, pure-logic check against an in-memory fake
``EmployeeRepository`` defined inline in this module (no shared conftest /
fakes module, to avoid collisions with the other onboarding property-test
modules). The fake mirrors the real repository's ``list`` signature and its
``is_active`` filter semantics: when ``is_active`` is ``True`` it returns only
the active records (and ``total`` is the count of active records), and it honors
``page`` / ``page_size`` pagination.

Validates: Requirements 7.1, 7.3, 7.4
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.onboarding.application.active_employee_query import ActiveEmployeeQuery

# Keep the generated population small enough that every active record fits on a
# single ``page_size = 50`` page, so the returned set equals the full active set.
_MAX_EMPLOYEES = 30
_PAGE_SIZE = 50


# ---------------------------------------------------------------------------
# In-memory fake (inline, module-private — no shared fixtures)
# ---------------------------------------------------------------------------
class FakeEmployeeRepo:
    """Minimal in-memory stand-in for ``EmployeeRepository``.

    Stores a list of :class:`Employee` records with varied ``is_active`` flags
    and reproduces the real repository's ``list`` contract: the ``is_active``
    filter, pagination by ``page`` / ``page_size``, and a ``(rows, total)``
    return shape where ``total`` is the count of records matching the filter.
    """

    def __init__(self, employees: list[Employee]) -> None:
        self.employees = employees

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        department_id: UUID | None = None,
        position_id: UUID | None = None,
        is_active: bool | None = True,
    ) -> tuple[list[Employee], int]:
        """Return a paginated, ``is_active``-filtered slice and the total count.

        Mirrors :meth:`EmployeeRepository.list`: when ``is_active`` is not
        ``None`` only records whose ``is_active`` equals it are considered; the
        full matching count is reported as ``total`` while the returned rows are
        limited to the requested page.
        """
        matching = self.employees
        if is_active is not None:
            matching = [emp for emp in matching if emp.is_active == is_active]

        total = len(matching)

        offset = (page - 1) * page_size
        page_rows = matching[offset : offset + page_size]
        return page_rows, total


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
def _build_employees(active_flags: list[bool]) -> list[Employee]:
    """Build Employee records with unique ids / codes / emails from flags."""
    employees: list[Employee] = []
    for index, is_active in enumerate(active_flags):
        employees.append(
            Employee(
                id=uuid4(),
                employee_code=f"NV-{index:03d}",
                full_name=f"Employee {index}",
                email=f"employee{index}@example.com",
                is_active=is_active,
            )
        )
    return employees


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------
async def _list_active(employees: list[Employee]) -> tuple[list[Employee], int]:
    """Run ``list_active`` against a fresh fake repo over ``employees``."""
    repo = FakeEmployeeRepo(employees)
    query = ActiveEmployeeQuery(repo)  # type: ignore[arg-type]
    return await query.list_active(page=1, page_size=_PAGE_SIZE)


# Feature: onboarding, Property 18: The active-Employee boundary includes exactly
# the active employees
@settings(max_examples=200, deadline=None)
@given(active_flags=st.lists(st.booleans(), min_size=0, max_size=_MAX_EMPLOYEES))
def test_active_employee_boundary_includes_exactly_active_employees(
    active_flags: list[bool],
) -> None:
    """The boundary list returns exactly the active employees and their count.

    Validates: Requirements 7.1, 7.3, 7.4
    """
    employees = _build_employees(active_flags)
    expected_active_ids = {emp.id for emp in employees if emp.is_active}

    returned, total = asyncio.run(_list_active(employees))
    returned_ids = {emp.id for emp in returned}

    # Every returned record is active — no is_active = False record leaks (R7.1).
    assert all(emp.is_active for emp in returned)

    # The returned set is exactly the set of active records (R7.1, R7.3, R7.4):
    # all active records are included and none are omitted (all fit one page).
    assert returned_ids == expected_active_ids

    # The reported total equals the number of active records.
    assert total == len(expected_active_ids)
