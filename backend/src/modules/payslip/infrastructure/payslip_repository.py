"""Repository for Payslip entity read operations.

Provides async database access for payslips using SQLAlchemy async
sessions with SQLModel. Only read operations — payslip creation is
an HR-admin concern handled separately.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.payslip.domain.entities import Payslip


class PayslipRepository:
    """Handles Payslip entity read operations.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, payslip_id: UUID) -> Payslip | None:
        """Retrieve a payslip by its ID.

        Args:
            payslip_id: The UUID of the payslip.

        Returns:
            The Payslip if found, None otherwise.
        """
        statement = select(Payslip).where(Payslip.id == payslip_id)  # type: ignore[arg-type]
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_published_by_id(self, payslip_id: UUID) -> Payslip | None:
        """Retrieve a published payslip by its ID.

        Args:
            payslip_id: The UUID of the payslip.

        Returns:
            The Payslip if found and published, None otherwise.
        """
        statement = select(Payslip).where(
            Payslip.id == payslip_id,  # type: ignore[arg-type]
            Payslip.published.is_(True),  # type: ignore[arg-type]
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_employee(self, employee_id: UUID) -> list[Payslip]:
        """List all published payslips for an employee.

        Args:
            employee_id: The UUID of the employee.

        Returns:
            List of published Payslip entities ordered by period descending.
        """
        statement = (
            select(Payslip)
            .where(
                Payslip.employee_id == employee_id,  # type: ignore[arg-type]
                Payslip.published.is_(True),  # type: ignore[arg-type]
            )
            .order_by(Payslip.pay_period_start.desc())  # type: ignore[arg-type]
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
