"""Unit tests for EmployeeService."""

import re
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.modules.employee.application.employee_service import EmployeeService
from src.modules.employee.domain.entities import Department, Employee, Position
from src.modules.employee.domain.exceptions import (
    DepartmentNotFoundError,
    DuplicateEmailError,
    EmployeeNotFoundError,
    PositionNotFoundError,
)


@pytest.fixture
def employee_repo() -> AsyncMock:
    """Create a mock EmployeeRepository."""
    return AsyncMock()


@pytest.fixture
def department_repo() -> AsyncMock:
    """Create a mock DepartmentRepository."""
    return AsyncMock()


@pytest.fixture
def position_repo() -> AsyncMock:
    """Create a mock PositionRepository."""
    return AsyncMock()


@pytest.fixture
def service(
    employee_repo: AsyncMock,
    department_repo: AsyncMock,
    position_repo: AsyncMock,
) -> EmployeeService:
    """Create an EmployeeService with mocked repositories."""
    return EmployeeService(
        employee_repository=employee_repo,
        department_repository=department_repo,
        position_repository=position_repo,
    )


class TestListEmployees:
    """Tests for EmployeeService.list_employees."""

    async def test_delegates_to_repository(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """list_employees delegates to repository with correct params."""
        employee_repo.list.return_value = ([], 0)

        result = await service.list_employees(
            page=2, page_size=10, search="test", department_id=None
        )

        employee_repo.list.assert_called_once_with(
            page=2,
            page_size=10,
            search="test",
            department_id=None,
            position_id=None,
            is_active=True,
        )
        assert result == ([], 0)

    async def test_returns_employees_and_total(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """list_employees returns the tuple from repository."""
        mock_employee = AsyncMock(spec=Employee)
        employee_repo.list.return_value = ([mock_employee], 1)

        items, total = await service.list_employees()

        assert len(items) == 1
        assert total == 1


class TestGetEmployee:
    """Tests for EmployeeService.get_employee."""

    async def test_returns_employee_when_found(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """get_employee returns the employee entity when found."""
        emp_id = uuid4()
        mock_employee = AsyncMock(spec=Employee)
        employee_repo.get_by_id.return_value = mock_employee

        result = await service.get_employee(emp_id)

        assert result == mock_employee
        employee_repo.get_by_id.assert_called_once_with(emp_id)

    async def test_raises_not_found_when_missing(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """get_employee raises EmployeeNotFoundError when not found."""
        employee_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeNotFoundError):
            await service.get_employee(uuid4())


class TestCreateEmployee:
    """Tests for EmployeeService.create_employee."""

    async def test_creates_employee_with_generated_code(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """create_employee auto-generates employee_code via repository."""
        employee_repo.get_by_email.return_value = None
        employee_repo.get_next_code.return_value = "NV-001"
        employee_repo.create.return_value = AsyncMock(spec=Employee)

        data = {"full_name": "Nguyen Van A", "email": "a@example.com"}
        await service.create_employee(data)

        employee_repo.get_next_code.assert_called_once()
        employee_repo.create.assert_called_once()
        created_employee = employee_repo.create.call_args[0][0]
        assert created_employee.employee_code == "NV-001"

    async def test_employee_code_follows_nv_xxx_format(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """create_employee assigns code matching NV-XXX format (Req 6.1)."""
        employee_repo.get_by_email.return_value = None
        employee_repo.get_next_code.return_value = "NV-042"
        employee_repo.create.return_value = AsyncMock(spec=Employee)

        data = {"full_name": "Tran Van B", "email": "b@example.com"}
        await service.create_employee(data)

        created_employee = employee_repo.create.call_args[0][0]
        # Verify NV-XXX format: "NV-" followed by 3+ digits
        assert re.match(r"^NV-\d{3,}$", created_employee.employee_code)

    async def test_sequential_code_generation(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """create_employee generates sequential codes (NV-001, NV-002, etc.) (Req 6.1)."""
        employee_repo.get_by_email.return_value = None
        employee_repo.create.return_value = AsyncMock(spec=Employee)

        # Simulate sequential code generation
        employee_repo.get_next_code.side_effect = ["NV-001", "NV-002", "NV-003"]

        for i, email in enumerate(
            ["first@example.com", "second@example.com", "third@example.com"], start=1
        ):
            await service.create_employee({"full_name": f"Employee {i}", "email": email})

        # Verify all three codes were assigned sequentially
        codes = [
            employee_repo.create.call_args_list[i][0][0].employee_code for i in range(3)
        ]
        assert codes == ["NV-001", "NV-002", "NV-003"]

    async def test_raises_duplicate_email_error(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """create_employee raises DuplicateEmailError if email exists."""
        employee_repo.get_by_email.return_value = AsyncMock(spec=Employee)

        with pytest.raises(DuplicateEmailError):
            await service.create_employee(
                {"full_name": "Test", "email": "existing@example.com"}
            )

    async def test_raises_department_not_found(
        self,
        service: EmployeeService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
    ) -> None:
        """create_employee raises DepartmentNotFoundError if dept doesn't exist."""
        employee_repo.get_by_email.return_value = None
        department_repo.get_by_id.return_value = None

        with pytest.raises(DepartmentNotFoundError):
            await service.create_employee(
                {
                    "full_name": "Test",
                    "email": "test@example.com",
                    "department_id": uuid4(),
                }
            )

    async def test_raises_position_not_found(
        self,
        service: EmployeeService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
        position_repo: AsyncMock,
    ) -> None:
        """create_employee raises PositionNotFoundError if position doesn't exist."""
        employee_repo.get_by_email.return_value = None
        department_repo.get_by_id.return_value = AsyncMock(spec=Department)
        position_repo.get_by_id.return_value = None

        with pytest.raises(PositionNotFoundError):
            await service.create_employee(
                {
                    "full_name": "Test",
                    "email": "test@example.com",
                    "department_id": uuid4(),
                    "position_id": uuid4(),
                }
            )

    async def test_creates_with_valid_department_and_position(
        self,
        service: EmployeeService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
        position_repo: AsyncMock,
    ) -> None:
        """create_employee succeeds when department and position exist."""
        dept_id = uuid4()
        pos_id = uuid4()
        employee_repo.get_by_email.return_value = None
        employee_repo.get_next_code.return_value = "NV-005"
        employee_repo.create.return_value = AsyncMock(spec=Employee)
        department_repo.get_by_id.return_value = AsyncMock(spec=Department)
        position_repo.get_by_id.return_value = AsyncMock(spec=Position)

        await service.create_employee(
            {
                "full_name": "Tran Thi B",
                "email": "b@example.com",
                "department_id": dept_id,
                "position_id": pos_id,
            }
        )

        employee_repo.create.assert_called_once()
        created = employee_repo.create.call_args[0][0]
        assert created.employee_code == "NV-005"
        assert created.department_id == dept_id
        assert created.position_id == pos_id


class TestUpdateEmployee:
    """Tests for EmployeeService.update_employee."""

    async def test_raises_not_found_when_employee_missing(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """update_employee raises EmployeeNotFoundError if not found."""
        employee_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeNotFoundError):
            await service.update_employee(uuid4(), {"full_name": "New Name"})

    async def test_raises_duplicate_email_on_change(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """update_employee raises DuplicateEmailError if new email is taken (Req 2.2)."""
        emp_id = uuid4()
        existing_employee = AsyncMock(spec=Employee)
        existing_employee.email = "old@example.com"
        employee_repo.get_by_id.return_value = existing_employee
        employee_repo.get_by_email.return_value = AsyncMock(spec=Employee)

        with pytest.raises(DuplicateEmailError):
            await service.update_employee(emp_id, {"email": "taken@example.com"})

    async def test_raises_duplicate_email_case_insensitive(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """update_employee checks email uniqueness case-insensitively (Req 2.2)."""
        emp_id = uuid4()
        existing_employee = AsyncMock(spec=Employee)
        existing_employee.email = "user@example.com"
        employee_repo.get_by_id.return_value = existing_employee
        # Different case of same email should not trigger duplicate check
        employee_repo.update.return_value = existing_employee

        result = await service.update_employee(emp_id, {"email": "USER@example.com"})

        # Should not call get_by_email since it's the same email (case-insensitive)
        employee_repo.get_by_email.assert_not_called()
        assert result == existing_employee

    async def test_allows_same_email(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """update_employee does not raise if email is unchanged."""
        emp_id = uuid4()
        existing_employee = AsyncMock(spec=Employee)
        existing_employee.email = "same@example.com"
        employee_repo.get_by_id.return_value = existing_employee
        employee_repo.update.return_value = existing_employee

        result = await service.update_employee(emp_id, {"email": "same@example.com"})

        assert result == existing_employee

    async def test_validates_department_on_change(
        self,
        service: EmployeeService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
    ) -> None:
        """update_employee raises DepartmentNotFoundError if new dept doesn't exist."""
        emp_id = uuid4()
        existing_employee = AsyncMock(spec=Employee)
        existing_employee.email = "test@example.com"
        employee_repo.get_by_id.return_value = existing_employee
        department_repo.get_by_id.return_value = None

        with pytest.raises(DepartmentNotFoundError):
            await service.update_employee(emp_id, {"department_id": uuid4()})

    async def test_validates_position_on_change(
        self,
        service: EmployeeService,
        employee_repo: AsyncMock,
        position_repo: AsyncMock,
    ) -> None:
        """update_employee raises PositionNotFoundError if new position doesn't exist."""
        emp_id = uuid4()
        existing_employee = AsyncMock(spec=Employee)
        existing_employee.email = "test@example.com"
        employee_repo.get_by_id.return_value = existing_employee
        position_repo.get_by_id.return_value = None

        with pytest.raises(PositionNotFoundError):
            await service.update_employee(emp_id, {"position_id": uuid4()})


class TestDeleteEmployee:
    """Tests for EmployeeService.delete_employee."""

    async def test_raises_not_found_when_missing(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """delete_employee raises EmployeeNotFoundError if not found."""
        employee_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeNotFoundError):
            await service.delete_employee(uuid4())

    async def test_calls_soft_delete(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """delete_employee calls repository.soft_delete (not hard delete) (Req 2.5)."""
        emp_id = uuid4()
        mock_employee = AsyncMock(spec=Employee)
        employee_repo.get_by_id.return_value = mock_employee
        employee_repo.soft_delete.return_value = mock_employee

        result = await service.delete_employee(emp_id)

        employee_repo.soft_delete.assert_called_once_with(emp_id)
        assert result == mock_employee

    async def test_soft_delete_does_not_hard_delete(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """delete_employee uses soft_delete, never calls delete/remove (Req 2.5)."""
        emp_id = uuid4()
        mock_employee = AsyncMock(spec=Employee)
        mock_employee.is_active = True
        employee_repo.get_by_id.return_value = mock_employee

        # Simulate soft_delete returning employee with is_active=False
        soft_deleted_employee = AsyncMock(spec=Employee)
        soft_deleted_employee.is_active = False
        employee_repo.soft_delete.return_value = soft_deleted_employee

        result = await service.delete_employee(emp_id)

        # Verify soft_delete was called (sets is_active=False)
        employee_repo.soft_delete.assert_called_once_with(emp_id)
        assert result.is_active is False
        # Verify no hard delete method was called
        assert not hasattr(employee_repo, "delete") or not employee_repo.delete.called
        assert not hasattr(employee_repo, "remove") or not employee_repo.remove.called


class TestPromoteCandidate:
    """Tests for EmployeeService.promote_candidate."""

    async def test_links_to_existing_employee_by_email(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """promote_candidate links candidate_id to existing employee if email matches."""
        candidate_id = uuid4()
        existing_emp = AsyncMock(spec=Employee)
        existing_emp.id = uuid4()
        employee_repo.get_by_email.return_value = existing_emp
        employee_repo.update.return_value = existing_emp

        result = await service.promote_candidate(
            {
                "full_name": "Existing Person",
                "email": "existing@example.com",
                "candidate_id": candidate_id,
            }
        )

        employee_repo.update.assert_called_once_with(
            existing_emp.id, {"candidate_id": candidate_id}
        )
        assert result == existing_emp

    async def test_creates_new_employee_from_candidate(
        self, service: EmployeeService, employee_repo: AsyncMock
    ) -> None:
        """promote_candidate creates a new employee when email doesn't exist."""
        candidate_id = uuid4()
        # First call (in promote_candidate) returns None - no existing employee
        # Second call (in create_employee) also returns None - email is unique
        employee_repo.get_by_email.return_value = None
        employee_repo.get_next_code.return_value = "NV-010"
        employee_repo.create.return_value = AsyncMock(spec=Employee)

        await service.promote_candidate(
            {
                "full_name": "New Hire",
                "email": "newhire@example.com",
                "candidate_id": candidate_id,
                "phone": "0901234567",
            }
        )

        employee_repo.create.assert_called_once()
        created = employee_repo.create.call_args[0][0]
        assert created.full_name == "New Hire"
        assert created.email == "newhire@example.com"
        assert created.candidate_id == candidate_id
        assert created.phone == "0901234567"
        assert created.employee_code == "NV-010"
