"""Repository for Payslip entity operations.

Provides async database access for payslips using SQLAlchemy async
sessions with SQLModel.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.payslip.domain.entities import Payslip, PayslipStatus


class PayslipRepository:
    """Handles Payslip persistence operations.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

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
            Payslip.status == PayslipStatus.PUBLISHED,  # type: ignore[arg-type]
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
                Payslip.status == PayslipStatus.PUBLISHED,  # type: ignore[arg-type]
            )
            .order_by(
                Payslip.period_month.desc(),  # type: ignore[arg-type]
                Payslip.updated_at.desc(),  # type: ignore[arg-type]
            )
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def exists_for_employee_and_period(
        self,
        employee_id: UUID,
        period_month: date,
        exclude_id: UUID | None = None,
    ) -> bool:
        """Check if a payslip exists for an employee and period.

        Args:
            employee_id: The UUID of the employee.
            period_month: The period month to check.
            exclude_id: Optional payslip ID to exclude (for update).

        Returns:
            True if a payslip exists, False otherwise.
        """
        statement = select(Payslip).where(
            Payslip.employee_id == employee_id,  # type: ignore[arg-type]
            Payslip.period_month == period_month,  # type: ignore[arg-type]
        )
        if exclude_id is not None:
            statement = statement.where(Payslip.id != exclude_id)  # type: ignore[arg-type]
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    # ------------------------------------------------------------------
    # Admin write operations
    # ------------------------------------------------------------------

    async def create(
        self,
        employee_id: UUID,
        period_month: date,
        gross_salary: Decimal,
        deductions: Decimal,
        insurance_employee: Decimal,
        taxable_income: Decimal,
        pit_amount: Decimal,
        net_salary: Decimal,
        pdf_url: str | None = None,
    ) -> Payslip:
        """Create a new draft Payslip.

        Args:
            employee_id: The UUID of the employee.
            period_month: The pay period (year-month).
            gross_salary: Gross salary amount.
            deductions: Total deductions.
            insurance_employee: Employee insurance contribution.
            taxable_income: Taxable income amount.
            pit_amount: Personal income tax amount.
            net_salary: Net salary (take-home).
            pdf_url: Optional PDF URL.

        Returns:
            The created Payslip entity.
        """
        payslip = Payslip(
            employee_id=employee_id,
            period_month=period_month,
            gross_salary=gross_salary,
            deductions=deductions,
            insurance_employee=insurance_employee,
            taxable_income=taxable_income,
            pit_amount=pit_amount,
            net_salary=net_salary,
            pdf_url=pdf_url,
        )
        self.session.add(payslip)
        await self.session.flush()
        return payslip

    async def update(
        self,
        payslip_id: UUID,
        *,
        gross_salary: Decimal | None = None,
        deductions: Decimal | None = None,
        insurance_employee: Decimal | None = None,
        taxable_income: Decimal | None = None,
        pit_amount: Decimal | None = None,
        net_salary: Decimal | None = None,
        pdf_url: str | None = None,
    ) -> Payslip | None:
        """Update a draft Payslip fields. None fields are not updated.

        Args:
            payslip_id: The UUID of the payslip to update.
            gross_salary: Optional new gross salary.
            deductions: Optional new deductions.
            insurance_employee: Optional new insurance contribution.
            taxable_income: Optional new taxable income.
            pit_amount: Optional new PIT amount.
            net_salary: Optional new net salary.
            pdf_url: Optional new PDF URL.

        Returns:
            The updated Payslip if found, None otherwise.
        """
        payslip = await self.get_by_id(payslip_id)
        if payslip is None:
            return None

        if gross_salary is not None:
            payslip.gross_salary = gross_salary
        if deductions is not None:
            payslip.deductions = deductions
        if insurance_employee is not None:
            payslip.insurance_employee = insurance_employee
        if taxable_income is not None:
            payslip.taxable_income = taxable_income
        if pit_amount is not None:
            payslip.pit_amount = pit_amount
        if net_salary is not None:
            payslip.net_salary = net_salary
        if pdf_url is not None:
            payslip.pdf_url = pdf_url

        payslip.updated_at = datetime.now()
        await self.session.flush()
        return payslip

    async def publish(self, payslip_id: UUID) -> Payslip | None:
        """Publish a draft Payslip.

        Sets status to PUBLISHED and records published_at timestamp.

        Args:
            payslip_id: The UUID of the payslip to publish.

        Returns:
            The published Payslip if found, None otherwise.
        """
        payslip = await self.get_by_id(payslip_id)
        if payslip is None:
            return None

        payslip.status = PayslipStatus.PUBLISHED
        payslip.published_at = datetime.now()
        payslip.updated_at = datetime.now()
        await self.session.flush()
        return payslip

    async def delete(self, payslip_id: UUID) -> bool:
        """Delete a draft Payslip.

        Only draft payslips can be deleted.

        Args:
            payslip_id: The UUID of the payslip to delete.

        Returns:
            True if deleted, False if not found.
        """
        payslip = await self.get_by_id(payslip_id)
        if payslip is None:
            return False

        await self.session.delete(payslip)
        await self.session.flush()
        return True

    async def count_all(
        self,
        employee_id: UUID | None = None,
        status: PayslipStatus | None = None,
        period_month: date | None = None,
    ) -> int:
        """Count payslips with optional filters.

        Args:
            employee_id: Optional employee filter.
            status: Optional status filter.
            period_month: Optional period filter.

        Returns:
            Total matching records.
        """
        statement = select(func.count()).select_from(Payslip)  # type: ignore[arg-type]
        if employee_id is not None:
            statement = statement.where(Payslip.employee_id == employee_id)  # type: ignore[arg-type]
        if status is not None:
            statement = statement.where(Payslip.status == status)  # type: ignore[arg-type]
        if period_month is not None:
            statement = statement.where(Payslip.period_month == period_month)  # type: ignore[arg-type]
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        employee_id: UUID | None = None,
        status: PayslipStatus | None = None,
        period_month: date | None = None,
    ) -> list[Payslip]:
        """List payslips with optional filters, ordered by period descending.

        Args:
            page: Page number (1-based).
            page_size: Records per page.
            employee_id: Optional employee filter.
            status: Optional status filter.
            period_month: Optional period filter.

        Returns:
            List of Payslip entities.
        """
        offset = (page - 1) * page_size
        statement = select(Payslip)
        if employee_id is not None:
            statement = statement.where(Payslip.employee_id == employee_id)  # type: ignore[arg-type]
        if status is not None:
            statement = statement.where(Payslip.status == status)  # type: ignore[arg-type]
        if period_month is not None:
            statement = statement.where(Payslip.period_month == period_month)  # type: ignore[arg-type]
        statement = (
            statement.order_by(
                Payslip.period_month.desc(),  # type: ignore[arg-type]
                Payslip.updated_at.desc(),  # type: ignore[arg-type]
            )
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
