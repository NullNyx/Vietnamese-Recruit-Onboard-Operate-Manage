"""Application service for Department CRUD operations.

Orchestrates department creation, retrieval, update, and deletion by
coordinating with the DepartmentRepository and enforcing business rules
such as name uniqueness and cascade protection (cannot delete departments
with active employees).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src.modules.employee.domain.entities import Department
from src.modules.employee.domain.exceptions import (
    DepartmentHasEmployeesError,
    DepartmentNotFoundError,
    EmployeeError,
)

if TYPE_CHECKING:
    from src.modules.employee.infrastructure.department_repository import (
        DepartmentRepository,
    )


class DepartmentService:
    """Handles department business logic and coordinates persistence.

    Validates business rules (name uniqueness, cascade protection)
    before delegating to the repository for data access.

    Args:
        department_repository: Repository for department persistence.
    """

    def __init__(self, department_repository: DepartmentRepository) -> None:
        """Initialize DepartmentService with the department repository.

        Args:
            department_repository: Repository for department CRUD operations.
        """
        self._department_repo = department_repository

    async def list_departments(self) -> list[Department]:
        """Retrieve all departments ordered by name.

        Returns:
            A list of all Department entities sorted alphabetically.
        """
        return await self._department_repo.list_all()

    async def create_department(self, data: dict) -> Department:
        """Create a new department.

        Validates that the department name is unique before persisting.

        Args:
            data: Dictionary containing department fields:
                - name: Department name (required)
                - description: Optional description

        Returns:
            The newly created Department entity.

        Raises:
            EmployeeError: If a department with the same name already exists.
        """
        name = data["name"]

        # Validate name uniqueness
        existing = await self._department_repo.get_by_name(name)
        if existing is not None:
            raise EmployeeError("Department with this name already exists")

        department = Department(
            name=name,
            description=data.get("description"),
        )

        return await self._department_repo.create(department)

    async def update_department(self, department_id: UUID, data: dict) -> Department:
        """Update an existing department.

        Validates that the department exists and that the new name (if changed)
        is unique among other departments.

        Args:
            department_id: The UUID of the department to update.
            data: Dictionary of fields to update (name, description).

        Returns:
            The updated Department entity.

        Raises:
            DepartmentNotFoundError: If no department exists with the given ID.
            EmployeeError: If the new name is already taken by another department.
        """
        # Validate department exists
        department = await self._department_repo.get_by_id(department_id)
        if department is None:
            raise DepartmentNotFoundError()

        # Validate name uniqueness if name is being changed
        new_name = data.get("name")
        if new_name is not None and new_name.lower() != department.name.lower():
            existing = await self._department_repo.get_by_name(new_name)
            if existing is not None:
                raise EmployeeError("Department with this name already exists")

        # Persist updates
        updated = await self._department_repo.update(department_id, data)
        if updated is None:
            raise DepartmentNotFoundError()
        return updated

    async def delete_department(self, department_id: UUID) -> bool:
        """Delete a department after cascade protection check.

        Validates that the department exists and has no active employees
        before performing a hard delete.

        Args:
            department_id: The UUID of the department to delete.

        Returns:
            True if the department was successfully deleted.

        Raises:
            DepartmentNotFoundError: If no department exists with the given ID.
            DepartmentHasEmployeesError: If the department has active employees.
        """
        # Validate department exists
        department = await self._department_repo.get_by_id(department_id)
        if department is None:
            raise DepartmentNotFoundError()

        # Check cascade protection
        has_employees = await self._department_repo.has_active_employees(department_id)
        if has_employees:
            raise DepartmentHasEmployeesError()

        # Perform delete
        deleted = await self._department_repo.delete(department_id)
        if not deleted:
            raise DepartmentNotFoundError()
        return deleted
