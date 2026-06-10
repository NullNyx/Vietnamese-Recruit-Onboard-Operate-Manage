"""Repository for AttendanceRecord entity CRUD operations.

Provides async database access for attendance records using SQLAlchemy
async sessions with SQLModel.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.domain.entities import AttendanceRecord, AttendanceSource


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
            AttendanceRecord.employee_id == employee_id,  # type: ignore[arg-type]
            AttendanceRecord.work_date == work_date,  # type: ignore[arg-type]
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

    async def upsert_check_in(
        self,
        employee_id: UUID,
        work_date: date,
        check_in_at: datetime,
        client_ip: str,
        user_agent: str | None,
    ) -> AttendanceRecord:
        """Atomically insert a check-in record or return the existing one.

        Uses PostgreSQL ON CONFLICT to handle the unique constraint on
        (employee_id, work_date). If the record already exists, returns it
        without overwriting — no race condition possible.

        Args:
            employee_id: The employee UUID.
            work_date: The work date to upsert.
            check_in_at: The check-in timestamp.
            client_ip: The client IP for the new record.
            user_agent: The user agent for the new record.

        Returns:
            The AttendanceRecord (newly inserted or existing).
        """
        stmt = (
            pg_insert(AttendanceRecord)
            .values(
                id=uuid4(),
                employee_id=employee_id,
                work_date=work_date,
                check_in_at=check_in_at,
                check_in_ip=client_ip,
                check_in_user_agent=user_agent,
                source=AttendanceSource.WEB,
            )
            .on_conflict_do_nothing(
                index_elements=["employee_id", "work_date"],
            )
            .returning(AttendanceRecord)
        )

        result = await self.session.execute(stmt)
        inserted = result.scalar_one_or_none()

        if inserted is not None:
            await self.session.flush()
            return inserted

        # Record already existed — fetch and return it
        existing = await self.get_by_employee_and_date(employee_id, work_date)
        assert existing is not None, "upsert returned nothing and no existing record found"
        return existing

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
                AttendanceRecord.employee_id == employee_id,  # type: ignore[arg-type]
                AttendanceRecord.work_date >= start_date,  # type: ignore[arg-type]
                AttendanceRecord.work_date <= end_date,  # type: ignore[arg-type]
            )
            .order_by(AttendanceRecord.work_date)  # type: ignore[arg-type]
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, record_id: UUID) -> AttendanceRecord | None:
        """Retrieve an attendance record by its ID.

        Args:
            record_id: The UUID of the record.

        Returns:
            The AttendanceRecord if found, None otherwise.
        """
        statement = select(AttendanceRecord).where(
            AttendanceRecord.id == record_id,  # type: ignore[arg-type]
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        start_date: date,
        end_date: date,
        employee_id: UUID | None = None,
        status: Literal["checked_in", "completed"] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AttendanceRecord], int]:
        """List attendance records with filters and pagination.

        Args:
            start_date: Start date for filter range.
            end_date: End date for filter range.
            employee_id: Optional filter by employee ID.
            status: Optional filter by status (checked_in, completed).
            page: Page number (1-based).
            page_size: Records per page.

        Returns:
            Tuple of (list of AttendanceRecord, total count).
        """
        from sqlalchemy import func

        # Build base query
        base_query = select(AttendanceRecord).where(
            AttendanceRecord.work_date >= start_date,  # type: ignore[arg-type]
            AttendanceRecord.work_date <= end_date,  # type: ignore[arg-type]
        )

        count_query = (
            select(func.count())
            .select_from(AttendanceRecord)
            .where(
                AttendanceRecord.work_date >= start_date,  # type: ignore[arg-type]
                AttendanceRecord.work_date <= end_date,  # type: ignore[arg-type]
            )
        )

        # Apply filters
        if employee_id is not None:
            base_query = base_query.where(
                AttendanceRecord.employee_id == employee_id,  # type: ignore[arg-type]
            )
            count_query = count_query.where(
                AttendanceRecord.employee_id == employee_id,  # type: ignore[arg-type]
            )

        if status == "checked_in":
            base_query = base_query.where(
                AttendanceRecord.check_in_at.isnot(None),  # type: ignore[arg-type]
                AttendanceRecord.check_out_at.is_(None),  # type: ignore[arg-type]
            )
            count_query = count_query.where(
                AttendanceRecord.check_in_at.isnot(None),  # type: ignore[arg-type]
                AttendanceRecord.check_out_at.is_(None),  # type: ignore[arg-type]
            )
        elif status == "completed":
            base_query = base_query.where(
                AttendanceRecord.check_in_at.isnot(None),  # type: ignore[arg-type]
                AttendanceRecord.check_out_at.isnot(None),  # type: ignore[arg-type]
            )
            count_query = count_query.where(
                AttendanceRecord.check_in_at.isnot(None),  # type: ignore[arg-type]
                AttendanceRecord.check_out_at.isnot(None),  # type: ignore[arg-type]
            )

        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        base_query = (
            base_query.order_by(
                AttendanceRecord.work_date.desc(),  # type: ignore[arg-type]
                AttendanceRecord.created_at.desc(),  # type: ignore[arg-type]
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(base_query)
        records = list(result.scalars().all())

        return records, total
