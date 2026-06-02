"""Repository for PayrollRecord entity."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.attendance.domain.entities import PayrollRecord


class PayrollRepository:
    """Handles PayrollRecord entity persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_employee_month(
        self, employee_id: UUID, month: int, year: int
    ) -> PayrollRecord | None:
        """Get payroll record for a specific employee and month."""
        statement = (
            select(PayrollRecord)
            .where(PayrollRecord.employee_id == employee_id)
            .where(PayrollRecord.month == month)
            .where(PayrollRecord.year == year)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create(self, record: PayrollRecord) -> PayrollRecord:
        """Create a new payroll record."""
        self.session.add(record)
        await self.session.flush()
        return record

    async def update(self, record: PayrollRecord) -> PayrollRecord:
        """Update a payroll record."""
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.flush()
        return record

    async def lock_payroll(self, record: PayrollRecord, locked_by: UUID) -> PayrollRecord:
        """Lock a payroll record."""
        record.status = "locked"
        record.locked_by = locked_by
        record.locked_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_by_month(
        self,
        month: int,
        year: int,
        status: str | None = None,
    ) -> list[PayrollRecord]:
        """List all payroll records for a month."""
        statement = (
            select(PayrollRecord)
            .where(PayrollRecord.month == month)
            .where(PayrollRecord.year == year)
        )
        if status:
            statement = statement.where(PayrollRecord.status == status)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
