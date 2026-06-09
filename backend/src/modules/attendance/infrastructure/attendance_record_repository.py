"""Repository for AttendanceRecord entity CRUD operations.

Provides async database access for attendance records using SQLAlchemy
async sessions with SQLModel.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.domain.entities import AttendanceRecord


class AttendanceRecordRepository:
    """Handles AttendanceRecord entity persistence using async SQLAlchemy sessions.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: An SQLAlchemy AsyncSession instance for database operations.
        """
        self.session = session

    async def get_by_employee_and_date(
        self,
        employee_id: UUID,
        work_date: date,
    ) -> AttendanceRecord | None:
        """Retrieve an attendance record for a specific employee and date.

        Args:
            employee_id: The UUID of the employee.
            work_date: The work date to query.

        Returns:
            The AttendanceRecord if found, None otherwise.
        """
        statement = select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.work_date == work_date,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, record: AttendanceRecord) -> AttendanceRecord:
        """Create a new attendance record.

        Args:
            record: The AttendanceRecord to create.

        Returns:
            The created AttendanceRecord.
        """
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def update(self, record: AttendanceRecord) -> AttendanceRecord:
        """Update an existing attendance record.

        Args:
            record: The AttendanceRecord to update.

        Returns:
            The updated AttendanceRecord.
        """
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def get_by_employee_and_date_range(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[AttendanceRecord]:
        """Retrieve attendance records for an employee within a date range.

        Args:
            employee_id: The UUID of the employee.
            start_date: The start date (inclusive).
            end_date: The end date (inclusive).

        Returns:
            List of AttendanceRecord entities.
        """
        statement = (
            select(AttendanceRecord)
            .where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.work_date >= start_date,
                AttendanceRecord.work_date <= end_date,
            )
            .order_by(AttendanceRecord.work_date)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
