"""Unit tests for EmploymentEventService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.employee.application.employment_event_service import (
    EmploymentEventService,
)
from src.modules.employee.domain.employment_event import EmploymentEvent


@pytest.fixture
def event_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(event_repo: AsyncMock) -> EmploymentEventService:
    return EmploymentEventService(event_repo=event_repo)


class TestRecord:
    async def test_creates_event_and_returns(
        self, service: EmploymentEventService, event_repo: AsyncMock
    ) -> None:
        employee_id = uuid4()
        actor_id = uuid4()
        mock_event = AsyncMock(spec=EmploymentEvent)
        event_repo.create.return_value = mock_event

        result = await service.record(
            employee_id=employee_id,
            event_type="status_change",
            actor_hr_id=actor_id,
            before={"status": "active"},
            after={"status": "resigned"},
            note="voluntary",
        )

        assert result == mock_event
        event_repo.create.assert_called_once()
        created = event_repo.create.call_args[0][0]
        assert created.employee_id == employee_id
        assert created.event_type == "status_change"
        assert created.actor_hr_id == actor_id
        assert created.before_json == {"status": "active"}
        assert created.after_json == {"status": "resigned"}
        assert created.note == "voluntary"


class TestListByEmployee:
    async def test_delegates_to_repo(
        self, service: EmploymentEventService, event_repo: AsyncMock
    ) -> None:
        employee_id = uuid4()
        event_repo.list_by_employee.return_value = []

        result = await service.list_by_employee(employee_id)

        event_repo.list_by_employee.assert_called_once_with(employee_id)
        assert result == []
