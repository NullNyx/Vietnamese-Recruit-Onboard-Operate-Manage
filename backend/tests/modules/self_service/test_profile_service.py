"""Unit tests for ESSProfileService."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.employee.domain.entities import Department, Employee, Position
from src.modules.employee.domain.exceptions import EmployeeNotFoundError
from src.modules.self_service.api.schemas import ESSProfileUpdateRequest
from src.modules.self_service.application.ess_profile_service import (
    ALLOWED_UPDATE_FIELDS,
    ESSProfileService,
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
) -> ESSProfileService:
    """Create an ESSProfileService with mocked repositories."""
    return ESSProfileService(
        employee_repository=employee_repo,
        department_repository=department_repo,
        position_repository=position_repo,
    )


def _make_employee(**overrides) -> Employee:
    """Create a test Employee entity with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "employee_code": "NV-001",
        "full_name": "Nguyen Van A",
        "email": "a@example.com",
        "phone": "0901234567",
        "date_of_birth": date(1990, 5, 15),
        "gender": "male",
        "address": "123 Le Loi, HCMC",
        "department_id": uuid4(),
        "position_id": uuid4(),
        "start_date": date(2023, 1, 10),
        "id_number": "079123456789",
        "tax_code": "1234567890",
        "contract_type": "full_time",
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return Employee(**defaults)


class TestGetProfile:
    """Tests for ESSProfileService.get_profile."""

    async def test_returns_profile_with_all_fields(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
        position_repo: AsyncMock,
    ) -> None:
        """get_profile returns a complete profile response with department/position names."""
        dept_id = uuid4()
        pos_id = uuid4()
        employee = _make_employee(department_id=dept_id, position_id=pos_id)
        employee_repo.get_by_id.return_value = employee

        dept = Department(id=dept_id, name="Engineering")
        department_repo.get_by_id.return_value = dept

        pos = Position(id=pos_id, name="Senior Developer")
        position_repo.get_by_id.return_value = pos

        result = await service.get_profile(employee.id)

        assert result.full_name == "Nguyen Van A"
        assert result.email == "a@example.com"
        assert result.phone == "0901234567"
        assert result.date_of_birth == date(1990, 5, 15)
        assert result.gender == "male"
        assert result.address == "123 Le Loi, HCMC"
        assert result.department_name == "Engineering"
        assert result.position_name == "Senior Developer"
        assert result.start_date == date(2023, 1, 10)
        assert result.contract_type == "full_time"

    async def test_masks_id_number(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
        position_repo: AsyncMock,
    ) -> None:
        """get_profile masks id_number showing only last 4 characters."""
        employee = _make_employee(
            id_number="079123456789",
            department_id=None,
            position_id=None,
        )
        employee_repo.get_by_id.return_value = employee

        result = await service.get_profile(employee.id)

        assert result.id_number_masked == "********6789"

    async def test_masks_tax_code(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
        position_repo: AsyncMock,
    ) -> None:
        """get_profile masks tax_code showing only last 4 characters."""
        employee = _make_employee(
            tax_code="1234567890",
            department_id=None,
            position_id=None,
        )
        employee_repo.get_by_id.return_value = employee

        result = await service.get_profile(employee.id)

        assert result.tax_code_masked == "******7890"

    async def test_handles_none_sensitive_fields(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """get_profile returns None for masked fields when originals are None."""
        employee = _make_employee(
            id_number=None,
            tax_code=None,
            department_id=None,
            position_id=None,
        )
        employee_repo.get_by_id.return_value = employee

        result = await service.get_profile(employee.id)

        assert result.id_number_masked is None
        assert result.tax_code_masked is None

    async def test_handles_no_department(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """get_profile returns None department_name when no department assigned."""
        employee = _make_employee(department_id=None, position_id=None)
        employee_repo.get_by_id.return_value = employee

        result = await service.get_profile(employee.id)

        assert result.department_name is None

    async def test_handles_no_position(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
        department_repo: AsyncMock,
    ) -> None:
        """get_profile returns None position_name when no position assigned."""
        dept_id = uuid4()
        employee = _make_employee(department_id=dept_id, position_id=None)
        employee_repo.get_by_id.return_value = employee
        department_repo.get_by_id.return_value = Department(id=dept_id, name="HR")

        result = await service.get_profile(employee.id)

        assert result.position_name is None

    async def test_raises_not_found_when_employee_missing(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """get_profile raises EmployeeNotFoundError when employee doesn't exist."""
        employee_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeNotFoundError):
            await service.get_profile(uuid4())


class TestUpdateProfile:
    """Tests for ESSProfileService.update_profile."""

    async def test_updates_phone(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """update_profile successfully updates phone field."""
        emp_id = uuid4()
        employee = _make_employee(id=emp_id, department_id=None, position_id=None)
        employee_repo.get_by_id.return_value = employee
        employee_repo.update.return_value = employee

        data = ESSProfileUpdateRequest(phone="0912345678")
        result = await service.update_profile(emp_id, data)

        # Verify update was called with phone and updated_at
        employee_repo.update.assert_called_once()
        call_args = employee_repo.update.call_args
        assert call_args[0][0] == emp_id
        update_dict = call_args[0][1]
        assert update_dict["phone"] == "0912345678"
        assert "updated_at" in update_dict

    async def test_updates_address(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """update_profile successfully updates address field."""
        emp_id = uuid4()
        employee = _make_employee(id=emp_id, department_id=None, position_id=None)
        employee_repo.get_by_id.return_value = employee
        employee_repo.update.return_value = employee

        data = ESSProfileUpdateRequest(address="456 Nguyen Hue, HCMC")
        result = await service.update_profile(emp_id, data)

        call_args = employee_repo.update.call_args
        update_dict = call_args[0][1]
        assert update_dict["address"] == "456 Nguyen Hue, HCMC"

    async def test_updates_emergency_contact(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """update_profile successfully updates emergency_contact field."""
        emp_id = uuid4()
        employee = _make_employee(id=emp_id, department_id=None, position_id=None)
        employee_repo.get_by_id.return_value = employee
        employee_repo.update.return_value = employee

        data = ESSProfileUpdateRequest(emergency_contact="Tran Thi B - 0987654321")
        result = await service.update_profile(emp_id, data)

        call_args = employee_repo.update.call_args
        update_dict = call_args[0][1]
        assert update_dict["emergency_contact"] == "Tran Thi B - 0987654321"

    async def test_updates_multiple_allowed_fields(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """update_profile can update multiple allowed fields at once."""
        emp_id = uuid4()
        employee = _make_employee(id=emp_id, department_id=None, position_id=None)
        employee_repo.get_by_id.return_value = employee
        employee_repo.update.return_value = employee

        data = ESSProfileUpdateRequest(
            phone="0912345678",
            address="789 Hai Ba Trung",
            emergency_contact="Mom - 0901111111",
        )
        result = await service.update_profile(emp_id, data)

        call_args = employee_repo.update.call_args
        update_dict = call_args[0][1]
        assert update_dict["phone"] == "0912345678"
        assert update_dict["address"] == "789 Hai Ba Trung"
        assert update_dict["emergency_contact"] == "Mom - 0901111111"
        assert "updated_at" in update_dict

    async def test_records_updated_at_timestamp(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """update_profile sets updated_at to current UTC timestamp."""
        emp_id = uuid4()
        employee = _make_employee(id=emp_id, department_id=None, position_id=None)
        employee_repo.get_by_id.return_value = employee
        employee_repo.update.return_value = employee

        before = datetime.now(UTC)
        data = ESSProfileUpdateRequest(phone="0912345678")
        await service.update_profile(emp_id, data)
        after = datetime.now(UTC)

        call_args = employee_repo.update.call_args
        update_dict = call_args[0][1]
        updated_at = update_dict["updated_at"]
        assert before <= updated_at <= after

    async def test_no_update_when_no_fields_set(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """update_profile does not call repository update when no fields are provided."""
        emp_id = uuid4()
        employee = _make_employee(id=emp_id, department_id=None, position_id=None)
        employee_repo.get_by_id.return_value = employee

        data = ESSProfileUpdateRequest()
        await service.update_profile(emp_id, data)

        employee_repo.update.assert_not_called()

    async def test_raises_not_found_when_employee_missing(
        self,
        service: ESSProfileService,
        employee_repo: AsyncMock,
    ) -> None:
        """update_profile raises EmployeeNotFoundError when employee doesn't exist."""
        employee_repo.get_by_id.return_value = None

        data = ESSProfileUpdateRequest(phone="0912345678")
        with pytest.raises(EmployeeNotFoundError):
            await service.update_profile(uuid4(), data)

    async def test_allowed_update_fields_constant(self) -> None:
        """ALLOWED_UPDATE_FIELDS contains exactly the expected fields."""
        assert ALLOWED_UPDATE_FIELDS == {"phone", "address", "emergency_contact"}
