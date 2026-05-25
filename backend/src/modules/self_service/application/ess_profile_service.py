"""ESS Profile Service for viewing and updating employee profile data.

Provides self-service profile operations with field masking for sensitive data
and an allowlist-based update mechanism that restricts which fields employees
can modify.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from fastapi import HTTPException, status

from src.modules.employee.domain.exceptions import EmployeeNotFoundError
from src.modules.self_service.api.schemas import ESSProfileResponse, ESSProfileUpdateRequest
from src.modules.self_service.application.masking import mask_sensitive_field

if TYPE_CHECKING:
    from src.modules.employee.infrastructure.department_repository import (
        DepartmentRepository,
    )
    from src.modules.employee.infrastructure.employee_repository import (
        EmployeeRepository,
    )
    from src.modules.employee.infrastructure.position_repository import (
        PositionRepository,
    )

# Fields that employees are allowed to update via self-service
ALLOWED_UPDATE_FIELDS: frozenset[str] = frozenset({"phone", "address", "emergency_contact"})


class ESSProfileService:
    """Handles employee self-service profile viewing and updating.

    Fetches employee data with department/position joins, masks sensitive
    fields, and enforces an allowlist for profile updates.

    Args:
        employee_repository: Repository for employee data access.
        department_repository: Repository for department lookups.
        position_repository: Repository for position lookups.
    """

    def __init__(
        self,
        employee_repository: EmployeeRepository,
        department_repository: DepartmentRepository,
        position_repository: PositionRepository,
    ) -> None:
        """Initialize ESSProfileService with required repositories.

        Args:
            employee_repository: Repository for employee CRUD operations.
            department_repository: Repository for department lookups.
            position_repository: Repository for position lookups.
        """
        self._employee_repo = employee_repository
        self._department_repo = department_repository
        self._position_repo = position_repository

    async def get_profile(self, employee_id: UUID) -> ESSProfileResponse:
        """Fetch the employee profile with department/position names and masked sensitive fields.

        Retrieves the employee record, resolves department and position names
        via their respective repositories, and masks id_number and tax_code.

        Args:
            employee_id: The UUID of the authenticated employee.

        Returns:
            An ESSProfileResponse with all profile fields populated.

        Raises:
            EmployeeNotFoundError: If no employee exists with the given ID.
        """
        employee = await self._employee_repo.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError()

        # Resolve department name
        department_name: str | None = None
        if employee.department_id is not None:
            department = await self._department_repo.get_by_id(employee.department_id)
            if department is not None:
                department_name = department.name

        # Resolve position name
        position_name: str | None = None
        if employee.position_id is not None:
            position = await self._position_repo.get_by_id(employee.position_id)
            if position is not None:
                position_name = position.name

        # Mask sensitive fields
        id_number_masked = mask_sensitive_field(employee.id_number)
        tax_code_masked = mask_sensitive_field(employee.tax_code)

        return ESSProfileResponse(
            full_name=employee.full_name,
            email=employee.email,
            phone=employee.phone,
            date_of_birth=employee.date_of_birth,
            gender=employee.gender,
            address=employee.address,
            department_name=department_name,
            position_name=position_name,
            start_date=employee.start_date,
            contract_type=employee.contract_type,
            id_number_masked=id_number_masked,
            tax_code_masked=tax_code_masked,
        )

    async def update_profile(
        self, employee_id: UUID, data: ESSProfileUpdateRequest
    ) -> ESSProfileResponse:
        """Update allowed profile fields for the authenticated employee.

        Only fields in the allowlist {phone, address, emergency_contact} are
        accepted. Any attempt to modify restricted fields results in a 403.
        Records the updated_at timestamp on successful update.

        Args:
            employee_id: The UUID of the authenticated employee.
            data: The validated update request containing only allowed fields.

        Returns:
            The updated ESSProfileResponse.

        Raises:
            HTTPException: 403 if restricted fields are detected.
            EmployeeNotFoundError: If no employee exists with the given ID.
        """
        # Defense in depth: verify only allowed fields are present
        update_data: dict[str, Any] = data.model_dump(exclude_unset=True)

        # Check for any fields outside the allowlist
        disallowed_fields = set(update_data.keys()) - ALLOWED_UPDATE_FIELDS
        if disallowed_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FIELD_UPDATE_FORBIDDEN",
                    "message": f"Cannot modify restricted fields: {', '.join(sorted(disallowed_fields))}",
                },
            )

        # Verify employee exists
        employee = await self._employee_repo.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError()

        # Only proceed with update if there are fields to update
        if update_data:
            # Record updated_at timestamp
            update_data["updated_at"] = datetime.now(UTC)
            await self._employee_repo.update(employee_id, update_data)

        # Return the refreshed profile
        return await self.get_profile(employee_id)
