"""Repository for AttendanceRecord entity CRUD operations."""

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.attendance.domain.entities import AttendanceRecord


class AttendanceRepository:
    """Handles AttendanceRecord entity persistence using async SQLAlchemy sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, record: AttendanceRecord) -> AttendanceRecord:
        """Persist a new attendance record."""
        self.session.add(record)
        await self.session.flush()
        return record

    async def update(self, record: AttendanceRecord) -> AttendanceRecord:
        """Update an existing attendance record."""
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_by_id(self, record_id: UUID) -> AttendanceRecord | None:
        """Get attendance record by ID."""
        statement = select(AttendanceRecord).where(AttendanceRecord.id == record_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_by_employee_and_date(
        self, employee_id: UUID, record_date: date
    ) -> AttendanceRecord | None:
        """Get today's attendance record for an employee."""
        start_of_day = datetime.combine(record_date, datetime.min.time()).replace(tzinfo=UTC)
        end_of_day = datetime.combine(record_date, datetime.max.time()).replace(tzinfo=UTC)

        statement = (
            select(AttendanceRecord)
            .where(AttendanceRecord.employee_id == employee_id)
            .where(AttendanceRecord.checkin_time >= start_of_day)
            .where(AttendanceRecord.checkin_time <= end_of_day)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_by_employee(
        self,
        employee_id: UUID,
        month: int | None = None,
        year: int | None = None,
        page: int = 1,
        page_size: int = 31,
    ) -> tuple[list[AttendanceRecord], int]:
        """List attendance records for an employee with optional month/year filter."""
        statement = select(AttendanceRecord).where(AttendanceRecord.employee_id == employee_id)
        count_statement = select(func.count()).select_from(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee_id
        )

        if month and year:
            month_filter = func.extract("month", AttendanceRecord.checkin_time) == month
            year_filter = func.extract("year", AttendanceRecord.checkin_time) == year
            statement = statement.where(month_filter).where(year_filter)
            count_statement = count_statement.where(month_filter).where(year_filter)

        # Get total count
        count_result = await self.session.execute(count_statement)
        total = count_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)
        statement = statement.order_by(desc(AttendanceRecord.checkin_time))

        result = await self.session.execute(statement)
        return list(result.scalars().all()), total

    async def list_by_month(
        self,
        month: int,
        year: int,
        department_id: UUID | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[AttendanceRecord], int]:
        """List all attendance records for a month (HR view)."""
        from src.modules.employee.domain.entities import Employee

        statement = (
            select(AttendanceRecord)
            .join(Employee, AttendanceRecord.employee_id == Employee.id)
            .where(func.extract("month", AttendanceRecord.checkin_time) == month)
            .where(func.extract("year", AttendanceRecord.checkin_time) == year)
        )
        count_statement = (
            select(func.count())
            .select_from(AttendanceRecord)
            .join(Employee, AttendanceRecord.employee_id == Employee.id)
            .where(func.extract("month", AttendanceRecord.checkin_time) == month)
            .where(func.extract("year", AttendanceRecord.checkin_time) == year)
        )

        if department_id:
            statement = statement.where(Employee.department_id == department_id)
            count_statement = count_statement.where(Employee.department_id == department_id)

        # Get total count
        count_result = await self.session.execute(count_statement)
        total = count_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)
        statement = statement.order_by(AttendanceRecord.checkin_time)

        result = await self.session.execute(statement)
        return list(result.scalars().all()), total
