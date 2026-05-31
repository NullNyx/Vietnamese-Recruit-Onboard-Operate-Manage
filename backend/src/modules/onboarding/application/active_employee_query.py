"""Active-Employee boundary query/guard for the Onboarding module.

This module implements the *boundary contract* between onboarding and the
active-Employee side of the system. Per the design Scope, the self-service
(ESS) module itself is out of scope; what is in scope is the contract that
"active-Employee queries must filter on ``is_active``", verified here at the
Employee-query layer.

:class:`ActiveEmployeeQuery` is a thin guard that wraps the reused
``EmployeeRepository`` (the Employee-query layer) and enforces two guarantees
for any active-Employee / self-service caller:

* **List boundary (R7.1, R7.3, R7.4):** :meth:`list_active` returns only
  Employee records with ``is_active = true`` and omits every record with
  ``is_active = false``. Because the filter is applied at read time, an Employee
  newly activated by onboarding completion becomes visible as soon as the
  activation transaction commits, and one still in onboarding never appears.
* **Access boundary (R7.2):** :meth:`get_active_by_id` returns the targeted
  Employee only when it is active; a request targeting an ``is_active = false``
  Employee is rejected with :class:`InactiveEmployeeAccessError` and the record
  is left unchanged (the guard performs no writes).

The guard owns no transaction and performs no mutations; it is a read-side
boundary that the future self-service module consumes.
"""

from __future__ import annotations

from uuid import UUID

from src.modules.employee.domain.entities import Employee
from src.modules.employee.domain.exceptions import EmployeeNotFoundError
from src.modules.employee.infrastructure.employee_repository import EmployeeRepository
from src.modules.onboarding.domain.exceptions import InactiveEmployeeAccessError

# Default page size for the active-Employee boundary list. Mirrors the
# onboarding list cap (``ONBOARDING_LIST_PAGE_SIZE_MAX``) so a single page
# request never returns more than the agreed maximum.
DEFAULT_ACTIVE_LIST_PAGE_SIZE = 50


class ActiveEmployeeQuery:
    """Boundary guard exposing only active Employees to self-service callers.

    Wraps the reused :class:`EmployeeRepository` and applies the
    onboarding/active-Employee boundary contract at the Employee-query layer.
    The guard is read-only: it never mutates an Employee record, so rejecting
    access to an inactive Employee leaves that record unchanged (R7.2).

    Attributes:
        employee_repo: The reused employee-module repository used as the
            Employee-query layer for the boundary.
    """

    def __init__(self, employee_repo: EmployeeRepository) -> None:
        """Initialize the guard with the Employee-query repository.

        Args:
            employee_repo: The reused :class:`EmployeeRepository` providing the
                Employee-query layer (paginated ``list`` and ``get_by_id``).
        """
        self.employee_repo = employee_repo

    async def list_active(
        self,
        page: int = 1,
        page_size: int = DEFAULT_ACTIVE_LIST_PAGE_SIZE,
        search: str | None = None,
        department_id: UUID | None = None,
        position_id: UUID | None = None,
    ) -> tuple[list[Employee], int]:
        """Return the active Employees visible to the active-Employee side.

        Delegates to :meth:`EmployeeRepository.list` with the ``is_active``
        filter pinned to ``True`` so the result contains only ``is_active =
        true`` records and omits every inactive record (R7.1, R7.4). Filtering
        happens at read time, so a newly activated Employee appears as soon as
        its activation transaction commits (R7.3).

        Args:
            page: The 1-indexed page number to retrieve.
            page_size: Maximum number of records to return for the page.
            search: Optional case-insensitive text matched against
                ``full_name`` or ``email``.
            department_id: Optional department filter.
            position_id: Optional position filter.

        Returns:
            A tuple ``(employees, total)`` where ``employees`` contains only
            active records for the requested page and ``total`` is the count of
            active records matching the filters.
        """
        return await self.employee_repo.list(
            page=page,
            page_size=page_size,
            search=search,
            department_id=department_id,
            position_id=position_id,
            is_active=True,
        )

    async def get_active_by_id(self, employee_id: UUID) -> Employee:
        """Return an Employee by id only when it is active, else reject access.

        Implements the access boundary for a self-service request that targets a
        specific Employee record:

        * If no Employee exists for ``employee_id``, raises
          :class:`EmployeeNotFoundError` (the record cannot be retrieved through
          the self-service side, R7.1).
        * If the Employee exists but has ``is_active = false``, raises
          :class:`InactiveEmployeeAccessError` and leaves the record unchanged
          (R7.2) — the guard performs no writes.
        * Otherwise (``is_active = true``) returns the Employee so the request is
          accepted (R7.4).

        Args:
            employee_id: The identifier of the Employee the self-service request
                targets.

        Returns:
            The active Employee record.

        Raises:
            EmployeeNotFoundError: If no Employee exists for ``employee_id``.
            InactiveEmployeeAccessError: If the Employee exists but is not
                active; the record is left unchanged.
        """
        employee = await self.employee_repo.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError()
        if not employee.is_active:
            raise InactiveEmployeeAccessError(employee_id)
        return employee
