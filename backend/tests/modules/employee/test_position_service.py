"""Unit tests for PositionService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.employee.application.position_service import PositionService
from src.modules.employee.domain.entities import Position
from src.modules.employee.domain.exceptions import (
    EmployeeError,
    PositionHasEmployeesError,
    PositionNotFoundError,
)


@pytest.fixture
def position_repo() -> AsyncMock:
    """Create a mocked PositionRepository."""
    return AsyncMock()


@pytest.fixture
def service(position_repo: AsyncMock) -> PositionService:
    """Create a PositionService with mocked repository."""
    return PositionService(position_repository=position_repo)


class TestListPositions:
    """Tests for PositionService.list_positions."""

    @pytest.mark.asyncio
    async def test_delegates_to_repository(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """list_positions delegates to repository.list_all."""
        positions = [
            Position(name="Senior Developer"),
            Position(name="Manager"),
        ]
        position_repo.list_all.return_value = positions

        result = await service.list_positions()

        position_repo.list_all.assert_called_once()
        assert result == positions

    @pytest.mark.asyncio
    async def test_returns_empty_list(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """list_positions returns empty list when no positions exist."""
        position_repo.list_all.return_value = []

        result = await service.list_positions()

        assert result == []


class TestCreatePosition:
    """Tests for PositionService.create_position."""

    @pytest.mark.asyncio
    async def test_creates_position_with_unique_name(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Successfully creates a position when name is unique."""
        dept_id = uuid4()
        position_repo.get_by_name.return_value = None
        expected = Position(name="Senior Developer", department_id=dept_id)
        position_repo.create.return_value = expected

        result = await service.create_position(
            {"name": "Senior Developer", "department_id": dept_id}
        )

        position_repo.get_by_name.assert_called_once_with("Senior Developer")
        assert result == expected

    @pytest.mark.asyncio
    async def test_creates_position_without_department(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Successfully creates a position without a department_id."""
        position_repo.get_by_name.return_value = None
        expected = Position(name="Consultant", department_id=None)
        position_repo.create.return_value = expected

        result = await service.create_position({"name": "Consultant"})

        assert result == expected

    @pytest.mark.asyncio
    async def test_raises_error_on_duplicate_name(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Raises EmployeeError when position name already exists."""
        position_repo.get_by_name.return_value = Position(name="Manager")

        with pytest.raises(EmployeeError, match="Position with this name already exists"):
            await service.create_position({"name": "Manager"})

        position_repo.create.assert_not_called()


class TestUpdatePosition:
    """Tests for PositionService.update_position."""

    @pytest.mark.asyncio
    async def test_updates_position_successfully(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Successfully updates a position when it exists and name is unique."""
        pos_id = uuid4()
        existing = Position(id=pos_id, name="Developer")
        position_repo.get_by_id.return_value = existing
        position_repo.get_by_name.return_value = None
        updated = Position(id=pos_id, name="Senior Developer")
        position_repo.update.return_value = updated

        result = await service.update_position(pos_id, {"name": "Senior Developer"})

        position_repo.get_by_id.assert_called_once_with(pos_id)
        position_repo.get_by_name.assert_called_once_with("Senior Developer")
        assert result == updated

    @pytest.mark.asyncio
    async def test_raises_not_found_when_position_missing(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Raises PositionNotFoundError when position doesn't exist."""
        pos_id = uuid4()
        position_repo.get_by_id.return_value = None

        with pytest.raises(PositionNotFoundError):
            await service.update_position(pos_id, {"name": "New Name"})

    @pytest.mark.asyncio
    async def test_raises_error_on_duplicate_name(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Raises EmployeeError when new name conflicts with another position."""
        pos_id = uuid4()
        existing = Position(id=pos_id, name="Developer")
        position_repo.get_by_id.return_value = existing
        position_repo.get_by_name.return_value = Position(
            id=uuid4(), name="Manager"
        )

        with pytest.raises(EmployeeError, match="Position with this name already exists"):
            await service.update_position(pos_id, {"name": "Manager"})

        position_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_uniqueness_check_when_name_unchanged(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Does not check name uniqueness when name is not being changed."""
        pos_id = uuid4()
        dept_id = uuid4()
        existing = Position(id=pos_id, name="Developer")
        position_repo.get_by_id.return_value = existing
        updated = Position(id=pos_id, name="Developer", department_id=dept_id)
        position_repo.update.return_value = updated

        result = await service.update_position(
            pos_id, {"department_id": dept_id}
        )

        position_repo.get_by_name.assert_not_called()
        assert result == updated


class TestDeletePosition:
    """Tests for PositionService.delete_position."""

    @pytest.mark.asyncio
    async def test_deletes_position_successfully(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Successfully deletes a position with no active employees."""
        pos_id = uuid4()
        position_repo.get_by_id.return_value = Position(id=pos_id, name="Old Position")
        position_repo.has_active_employees.return_value = False
        position_repo.delete.return_value = True

        result = await service.delete_position(pos_id)

        position_repo.has_active_employees.assert_called_once_with(pos_id)
        position_repo.delete.assert_called_once_with(pos_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_raises_not_found_when_position_missing(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Raises PositionNotFoundError when position doesn't exist."""
        pos_id = uuid4()
        position_repo.get_by_id.return_value = None

        with pytest.raises(PositionNotFoundError):
            await service.delete_position(pos_id)

        position_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_error_when_position_has_employees(
        self, service: PositionService, position_repo: AsyncMock
    ) -> None:
        """Raises PositionHasEmployeesError when position has active employees."""
        pos_id = uuid4()
        position_repo.get_by_id.return_value = Position(id=pos_id, name="Active Position")
        position_repo.has_active_employees.return_value = True

        with pytest.raises(PositionHasEmployeesError):
            await service.delete_position(pos_id)

        position_repo.delete.assert_not_called()
