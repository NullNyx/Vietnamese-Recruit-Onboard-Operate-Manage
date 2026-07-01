"""Application service for EmploymentEvent recording."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src.modules.employee.domain.employment_event import EmploymentEvent

if TYPE_CHECKING:
    from src.modules.employee.infrastructure.employment_event_repository import (
        EmploymentEventRepository,
    )


class EmploymentEventService:
    """Records and lists EmploymentEvents for audit trail."""

    def __init__(self, event_repo: EmploymentEventRepository) -> None:
        self._event_repo = event_repo

    async def record(
        self,
        employee_id: UUID,
        event_type: str,
        actor_hr_id: UUID,
        before: dict | None = None,
        after: dict | None = None,
        note: str | None = None,
    ) -> EmploymentEvent:
        event = EmploymentEvent(
            employee_id=employee_id,
            event_type=event_type,
            before_json=before,
            after_json=after,
            actor_hr_id=actor_hr_id,
            note=note,
        )
        return await self._event_repo.create(event)

    async def list_by_employee(self, employee_id: UUID) -> list[EmploymentEvent]:
        return await self._event_repo.list_by_employee(employee_id)
