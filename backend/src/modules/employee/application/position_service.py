"""Application service for Position CRUD operations.

Orchestrates position creation, retrieval, update, and deletion by
coordinating with the PositionRepository and enforcing business rules
such as name uniqueness and cascade protection (cannot delete positions
with active employees).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src.modules.employee.domain.entities import Position
from src.modules.employee.domain.exceptions import (
    EmployeeError,
    PositionHasEmployeesError,
    PositionNotFoundError,
)

if TYPE_CHECKING:
    from src.modules.employee.infrastructure.position_repository import (
        PositionRepository,
    )


class PositionService:
    """Handles position business logic and coordinates persistence.

    Validates business rules (name uniqueness, cascade protection)
    before delegating to the repository for data access.

    Args:
        position_repository: Repository for position persistence.
    """

    def __init__(self, position_repository: PositionRepository) -> None:
        """Initialize PositionService with the position repository.

        Args:
            position_repository: Repository for position CRUD operations.
        """
        self._position_repo = position_repository

    async def list_positions(self) -> list[Position]:
        """Retrieve all positions ordered by name.

        Returns:
            A list of all Position entities sorted alphabetically.
        """
        return await self._position_repo.list_all()

    async def create_position(self, data: dict) -> Position:
        """Create a new position.

        Validates that the position name is unique before persisting.

        Args:
            data: Dictionary containing position fields:
                - name: Position name (required)
                - department_id: Optional UUID linking to a department

        Returns:
            The newly created Position entity.

        Raises:
            EmployeeError: If a position with the same name already exists.
        """
        name = data["name"]

        # Validate name uniqueness
        existing = await self._position_repo.get_by_name(name)
        if existing is not None:
            raise EmployeeError("Position with this name already exists")

        position = Position(
            name=name,
            department_id=data.get("department_id"),
        )

        return await self._position_repo.create(position)

    async def update_position(self, position_id: UUID, data: dict) -> Position:
        """Update an existing position.

        Validates that the position exists and that the new name (if changed)
        is unique among other positions.

        Args:
            position_id: The UUID of the position to update.
            data: Dictionary of fields to update (name, department_id).

        Returns:
            The updated Position entity.

        Raises:
            PositionNotFoundError: If no position exists with the given ID.
            EmployeeError: If the new name is already taken by another position.
        """
        # Validate position exists
        position = await self._position_repo.get_by_id(position_id)
        if position is None:
            raise PositionNotFoundError()

        # Validate name uniqueness if name is being changed
        new_name = data.get("name")
        if new_name is not None and new_name.lower() != position.name.lower():
            existing = await self._position_repo.get_by_name(new_name)
            if existing is not None:
                raise EmployeeError("Position with this name already exists")

        # Persist updates
        updated = await self._position_repo.update(position_id, data)
        if updated is None:
            raise PositionNotFoundError()
        return updated

    async def delete_position(self, position_id: UUID) -> bool:
        """Delete a position after cascade protection check.

        Validates that the position exists and has no active employees
        before performing a hard delete.

        Args:
            position_id: The UUID of the position to delete.

        Returns:
            True if the position was successfully deleted.

        Raises:
            PositionNotFoundError: If no position exists with the given ID.
            PositionHasEmployeesError: If the position has active employees.
        """
        # Validate position exists
        position = await self._position_repo.get_by_id(position_id)
        if position is None:
            raise PositionNotFoundError()

        # Check cascade protection
        has_employees = await self._position_repo.has_active_employees(position_id)
        if has_employees:
            raise PositionHasEmployeesError()

        # Perform delete
        deleted = await self._position_repo.delete(position_id)
        if not deleted:
            raise PositionNotFoundError()
        return deleted
