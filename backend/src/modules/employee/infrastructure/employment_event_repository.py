"""Repository for EmploymentEvent entity CRUD operations."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.employee.domain.employment_event import EmploymentEvent


class EmploymentEventRepository:
    """Handles EmploymentEvent persistence using async SQLAlchemy sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, event: EmploymentEvent) -> EmploymentEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_by_employee(self, employee_id: UUID) -> list[EmploymentEvent]:
        stmt = (
            select(EmploymentEvent)
            .where(EmploymentEvent.employee_id == employee_id)
            .order_by(EmploymentEvent.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
