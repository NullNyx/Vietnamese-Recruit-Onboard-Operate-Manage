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

    async def get_published_by_id_and_employee(
        self,
        payslip_id: UUID,
        employee_id: UUID,
    ) -> Payslip | None:
        """Retrieve a published payslip for a specific employee by its ID.

        Fail-closed: only returns the payslip if it belongs to the given
        employee AND is published. Returns None otherwise.

        Args:
            payslip_id: The UUID of the payslip.
            employee_id: The UUID of the employee.

        Returns:
            The Payslip if found, published, and owned by employee; None otherwise.
        """
        statement = select(Payslip).where(
            Payslip.id == payslip_id,  # type: ignore[arg-type]
            Payslip.employee_id == employee_id,  # type: ignore[arg-type]
            Payslip.published.is_(True),  # type: ignore[arg-type]
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_employee(
        self,
        employee_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Payslip]:
        """List all published payslips for an employee.

        Args:
            employee_id: The UUID of the employee.
            page: Page number (1-based).
            page_size: Records per page (default 50).

        Returns:
            List of published Payslip entities ordered by period descending.
        """
        offset = (page - 1) * page_size
        statement = (
            select(Payslip)
            .where(
                Payslip.employee_id == employee_id,  # type: ignore[arg-type]
                Payslip.published.is_(True),  # type: ignore[arg-type]
            )
            .order_by(
                Payslip.pay_period_start.desc(),  # type: ignore[arg-type]
                Payslip.id.desc(),  # type: ignore[arg-type]
            )
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
