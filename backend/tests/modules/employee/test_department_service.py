"""Unit tests for DepartmentService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.employee.application.department_service import DepartmentService
from src.modules.employee.domain.entities import Department
from src.modules.employee.domain.exceptions import (
    DepartmentHasEmployeesError,
    DepartmentNotFoundError,
    EmployeeError,
)


@pytest.fixture
def department_repo() -> AsyncMock:
    """Create a mocked DepartmentRepository."""
    return AsyncMock()


@pytest.fixture
def service(department_repo: AsyncMock) -> DepartmentService:
    """Create a DepartmentService with mocked repository."""
    return DepartmentService(department_repository=department_repo)


class TestListDepartments:
    """Tests for DepartmentService.list_departments."""

    @pytest.mark.asyncio
    async def test_delegates_to_repository(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """list_departments delegates to repository.list_all."""
        departments = [
            Department(name="Engineering"),
            Department(name="HR"),
        ]
        department_repo.list_all.return_value = departments

        result = await service.list_departments()

        department_repo.list_all.assert_called_once()
        assert result == departments

    @pytest.mark.asyncio
    async def test_returns_empty_list(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """list_departments returns empty list when no departments exist."""
        department_repo.list_all.return_value = []

        result = await service.list_departments()

        assert result == []


class TestCreateDepartment:
    """Tests for DepartmentService.create_department."""

    @pytest.mark.asyncio
    async def test_creates_department_with_unique_name(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Successfully creates a department when name is unique."""
        department_repo.get_by_name.return_value = None
        expected = Department(name="Engineering", description="Tech team")
        department_repo.create.return_value = expected

        result = await service.create_department(
            {"name": "Engineering", "description": "Tech team"}
        )

        department_repo.get_by_name.assert_called_once_with("Engineering")
        assert result == expected

    @pytest.mark.asyncio
    async def test_raises_error_on_duplicate_name(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Raises EmployeeError when department name already exists."""
        department_repo.get_by_name.return_value = Department(name="Engineering")

        with pytest.raises(EmployeeError, match="Department with this name already exists"):
            await service.create_department({"name": "Engineering"})

        department_repo.create.assert_not_called()


class TestUpdateDepartment:
    """Tests for DepartmentService.update_department."""

    @pytest.mark.asyncio
    async def test_updates_department_successfully(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Successfully updates a department when it exists and name is unique."""
        dept_id = uuid4()
        existing = Department(id=dept_id, name="Engineering")
        department_repo.get_by_id.return_value = existing
        department_repo.get_by_name.return_value = None
        updated = Department(id=dept_id, name="Tech", description="Updated")
        department_repo.update.return_value = updated

        result = await service.update_department(dept_id, {"name": "Tech"})

        department_repo.get_by_id.assert_called_once_with(dept_id)
        department_repo.get_by_name.assert_called_once_with("Tech")
        assert result == updated

    @pytest.mark.asyncio
    async def test_raises_not_found_when_department_missing(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Raises DepartmentNotFoundError when department doesn't exist."""
        dept_id = uuid4()
        department_repo.get_by_id.return_value = None

        with pytest.raises(DepartmentNotFoundError):
            await service.update_department(dept_id, {"name": "New Name"})

    @pytest.mark.asyncio
    async def test_raises_error_on_duplicate_name(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Raises EmployeeError when new name conflicts with another department."""
        dept_id = uuid4()
        existing = Department(id=dept_id, name="Engineering")
        department_repo.get_by_id.return_value = existing
        department_repo.get_by_name.return_value = Department(id=uuid4(), name="HR")

        with pytest.raises(EmployeeError, match="Department with this name already exists"):
            await service.update_department(dept_id, {"name": "HR"})

        department_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_uniqueness_check_when_name_unchanged(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Does not check name uniqueness when name is not being changed."""
        dept_id = uuid4()
        existing = Department(id=dept_id, name="Engineering")
        department_repo.get_by_id.return_value = existing
        updated = Department(id=dept_id, name="Engineering", description="Updated desc")
        department_repo.update.return_value = updated

        result = await service.update_department(dept_id, {"description": "Updated desc"})

        department_repo.get_by_name.assert_not_called()
        assert result == updated


class TestDeleteDepartment:
    """Tests for DepartmentService.delete_department."""

    @pytest.mark.asyncio
    async def test_deletes_department_successfully(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Successfully deletes a department with no active employees."""
        dept_id = uuid4()
        department_repo.get_by_id.return_value = Department(id=dept_id, name="Old Dept")
        department_repo.has_active_employees.return_value = False
        department_repo.delete.return_value = True

        result = await service.delete_department(dept_id)

        department_repo.has_active_employees.assert_called_once_with(dept_id)
        department_repo.delete.assert_called_once_with(dept_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_raises_not_found_when_department_missing(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Raises DepartmentNotFoundError when department doesn't exist."""
        dept_id = uuid4()
        department_repo.get_by_id.return_value = None

        with pytest.raises(DepartmentNotFoundError):
            await service.delete_department(dept_id)

        department_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_error_when_department_has_employees(
        self, service: DepartmentService, department_repo: AsyncMock
    ) -> None:
        """Raises DepartmentHasEmployeesError when department has active employees."""
        dept_id = uuid4()
        department_repo.get_by_id.return_value = Department(id=dept_id, name="Active Dept")
        department_repo.has_active_employees.return_value = True

        with pytest.raises(DepartmentHasEmployeesError):
            await service.delete_department(dept_id)

        department_repo.delete.assert_not_called()
