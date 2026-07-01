"""Application service for Employee CRUD operations.

Orchestrates employee creation, retrieval, update, soft-delete, and
candidate promotion by coordinating between repositories and enforcing
business rules such as email uniqueness and referential integrity.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.modules.employee.domain.entities import Employee
from src.modules.employee.domain.exceptions import (
    DepartmentNotFoundError,
    DuplicateEmailError,
    EmployeeNotFoundError,
    InvalidStatusTransitionError,
    PositionNotFoundError,
)

if TYPE_CHECKING:
    from src.modules.employee.application.employment_event_service import (
        EmploymentEventService,
    )
    from src.modules.employee.infrastructure.department_repository import (
        DepartmentRepository,
    )
    from src.modules.employee.infrastructure.employee_repository import (
        EmployeeRepository,
    )
    from src.modules.employee.infrastructure.position_repository import (
        PositionRepository,
    )


class EmployeeService:
    """Handles employee business logic and coordinates persistence.

    Validates business rules (email uniqueness, department/position existence)
    before delegating to repositories for data access.

    Args:
        employee_repository: Repository for employee persistence.
        department_repository: Repository for department lookups.
        position_repository: Repository for position lookups.
    """

    def __init__(
        self,
        employee_repository: EmployeeRepository,
        department_repository: DepartmentRepository,
        position_repository: PositionRepository,
        event_service: EmploymentEventService | None = None,
    ) -> None:
        """Initialize EmployeeService with required repositories.

        Args:
            employee_repository: Repository for employee CRUD operations.
            department_repository: Repository for department lookups.
            position_repository: Repository for position lookups.
            event_service: Optional EmploymentEventService for audit trail.
        """
        self._employee_repo = employee_repository
        self._department_repo = department_repository
        self._position_repo = position_repository
        self._event_service = event_service

    async def list_employees(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        department_id: UUID | None = None,
        position_id: UUID | None = None,
        is_active: bool | None = True,
    ) -> tuple[list[Employee], int]:
        """Retrieve a paginated list of employees with optional filters.

        Args:
            page: The page number (1-indexed).
            page_size: Number of items per page.
            search: Optional text to search in full_name or email.
            department_id: Optional filter by department UUID.
            position_id: Optional filter by position UUID.
            is_active: Optional filter by active status. Defaults to True.

        Returns:
            A tuple of (list of Employee entities, total count).
        """
        return await self._employee_repo.list(
            page=page,
            page_size=page_size,
            search=search,
            department_id=department_id,
            position_id=position_id,
            is_active=is_active,
        )

    async def get_employee(self, employee_id: UUID) -> Employee:
        """Retrieve a single employee by ID.

        Args:
            employee_id: The UUID of the employee to retrieve.

        Returns:
            The Employee entity.

        Raises:
            EmployeeNotFoundError: If no employee exists with the given ID.
        """
        employee = await self._employee_repo.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError()
        return employee

    async def create_employee(self, data: dict[str, Any]) -> Employee:
        """Create a new employee with auto-generated employee code.

        Validates email uniqueness and department/position existence
        before persisting the new employee record.

        Args:
            data: Dictionary of employee fields (full_name, email, phone,
                date_of_birth, gender, address, department_id, position_id,
                start_date, id_number, tax_code, contract_type, candidate_id).

        Returns:
            The newly created Employee entity with generated employee_code.

        Raises:
            DuplicateEmailError: If an employee with the same email exists.
            DepartmentNotFoundError: If the specified department_id doesn't exist.
            PositionNotFoundError: If the specified position_id doesn't exist.
        """
        # Validate email uniqueness
        email = data.get("email")
        if email:
            existing = await self._employee_repo.get_by_email(email)
            if existing is not None:
                raise DuplicateEmailError()

        # Validate department exists if provided
        department_id = data.get("department_id")
        if department_id is not None:
            department = await self._department_repo.get_by_id(department_id)
            if department is None:
                raise DepartmentNotFoundError()

        # Validate position exists if provided
        position_id = data.get("position_id")
        if position_id is not None:
            position = await self._position_repo.get_by_id(position_id)
            if position is None:
                raise PositionNotFoundError()

        # Auto-generate employee code
        employee_code = await self._employee_repo.get_next_code()

        # Create employee entity
        employee = Employee(
            employee_code=employee_code,
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone"),
            date_of_birth=data.get("date_of_birth"),
            gender=data.get("gender"),
            address=data.get("address"),
            department_id=department_id,
            position_id=position_id,
            start_date=data.get("start_date"),
            id_number=data.get("id_number"),
            personal_tax_code=data.get("tax_code"),
            contract_type=data.get("contract_type"),
            candidate_id=data.get("candidate_id"),
        )

        return await self._employee_repo.create(employee)

    async def update_employee(
        self,
        employee_id: UUID,
        data: dict[str, Any],
        actor_hr_id: UUID | None = None,
    ) -> Employee:
        """Update an existing employee record.

        Validates that the employee exists, checks email uniqueness if
        email is being changed, and validates department/position existence
        if those fields are being updated.

        Args:
            employee_id: The UUID of the employee to update.
            data: Dictionary of fields to update.

        Returns:
            The updated Employee entity.

        Raises:
            EmployeeNotFoundError: If no employee exists with the given ID.
            DuplicateEmailError: If the new email is already taken by another employee.
            DepartmentNotFoundError: If the specified department_id doesn't exist.
            PositionNotFoundError: If the specified position_id doesn't exist.
        """
        # Validate employee exists
        employee = await self._employee_repo.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError()
        before = employee.model_dump(mode="json")

        # Validate email uniqueness if email is being changed
        new_email = data.get("email")
        if new_email is not None and new_email.lower() != employee.email.lower():
            existing = await self._employee_repo.get_by_email(new_email)
            if existing is not None:
                raise DuplicateEmailError()

        # Validate department exists if being changed
        if "department_id" in data and data["department_id"] is not None:
            department = await self._department_repo.get_by_id(data["department_id"])
            if department is None:
                raise DepartmentNotFoundError()

        # Validate position exists if being changed
        if "position_id" in data and data["position_id"] is not None:
            position = await self._position_repo.get_by_id(data["position_id"])
            if position is None:
                raise PositionNotFoundError()

        # Persist updates
        updated = await self._employee_repo.update(employee_id, data)
        if updated is None:
            raise EmployeeNotFoundError()
        if self._event_service and actor_hr_id is not None:
            await self._event_service.record(
                employee_id=employee_id,
                event_type="profile_update",
                actor_hr_id=actor_hr_id,
                before=before,
                after=updated.model_dump(mode="json"),
            )
        return updated

    async def delete_employee(self, employee_id: UUID) -> Employee:
        """Soft-delete an employee by setting is_active=False.

        Args:
            employee_id: The UUID of the employee to soft-delete.

        Returns:
            The soft-deleted Employee entity.

        Raises:
            EmployeeNotFoundError: If no employee exists with the given ID.
        """
        # Validate employee exists
        employee = await self._employee_repo.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError()

        deleted = await self._employee_repo.soft_delete(employee_id)
        if deleted is None:
            raise EmployeeNotFoundError()
        return deleted

    async def change_status(
        self,
        employee_id: UUID,
        new_status: str,
        actor_hr_id: UUID,
        termination_date: date | None = None,
        note: str | None = None,
    ) -> Employee:
        """Change an employee's employment status with event recording."""
        employee = await self.get_employee(employee_id)

        # Basic transition validation
        allowed = ("active", "resigned", "terminated", "suspended")
        if new_status not in allowed:
            raise InvalidStatusTransitionError()

        before = {"employment_status": employee.employment_status}
        updated = await self._employee_repo.update_status(
            employee_id, new_status, termination_date
        )
        if updated is None:
            raise EmployeeNotFoundError()

        if self._event_service:
            await self._event_service.record(
                employee_id=employee_id,
                event_type="status_change",
                actor_hr_id=actor_hr_id,
                before=before,
                after={"employment_status": new_status},
                note=note,
            )
        return updated

    async def promote_candidate(self, data: dict[str, Any]) -> Employee:
        """Create an employee from a promoted candidate.

        Accepts candidate data and creates an employee record with source
        tracking via the candidate_id field. If the candidate's email
        already exists as an employee, links the candidate to the existing
        employee record instead of creating a duplicate.

        Args:
            data: Dictionary containing candidate information:
                - full_name: Candidate's full name (required)
                - email: Candidate's email (required)
                - candidate_id: UUID of the candidate for traceability (required)
                - phone: Candidate's phone number (optional)
                - department_id: Target department UUID (optional)
                - position_id: Target position UUID (optional)
                - start_date: Employment start date (optional)

        Returns:
            The Employee entity (newly created or existing with updated candidate_id).

        Raises:
            DepartmentNotFoundError: If the specified department_id doesn't exist.
            PositionNotFoundError: If the specified position_id doesn't exist.
        """
        email = data.get("email")
        candidate_id = data.get("candidate_id")

        # Check if employee with this email already exists
        if email:
            existing = await self._employee_repo.get_by_email(email)
            if existing is not None:
                # Link candidate to existing employee record
                update_data = {"candidate_id": candidate_id}
                updated = await self._employee_repo.update(existing.id, update_data)
                if updated is None:
                    raise EmployeeNotFoundError()
                return updated

        # Create new employee from candidate data
        create_data = {
            "full_name": data["full_name"],
            "email": data["email"],
            "phone": data.get("phone"),
            "department_id": data.get("department_id"),
            "position_id": data.get("position_id"),
            "start_date": data.get("start_date"),
            "candidate_id": candidate_id,
        }

        return await self.create_employee(create_data)
