"""Application service for HR Payslip management.

Handles create, update, publish, and delete of Payslips by HR (admin).
All mutations are audited. Enforces:
- At most one active payslip per Employee per period_month
- Only draft payslips can be updated or deleted
- Published payslips are immutable
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.domain.entities import AuditActionType, User
from src.modules.payslip.domain.entities import Payslip, PayslipStatus
from src.modules.payslip.domain.exceptions import (
    PayslipAlreadyExistsError,
    PayslipAlreadyPublishedError,
    PayslipNotDraftError,
    PayslipNotFoundError,
)
from src.modules.payslip.infrastructure.payslip_repository import PayslipRepository


class PayslipHRService:
    """Service for HR payslip admin operations.

    All operations require an authenticated admin user.
    Every mutating action is recorded in the audit log.
    """

    def __init__(
        self,
        payslip_repo: PayslipRepository,
        audit_service: AuditService,
    ) -> None:
        self._payslip_repo = payslip_repo
        self._audit_service = audit_service

    async def create_draft(
        self,
        admin: User,
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
        """Create a new draft Payslip for an Employee and period.

        Enforces uniqueness: at most one payslip per Employee per period.

        Args:
            admin: The admin performing the action.
            employee_id: The UUID of the employee.
            period_month: The pay period (year-month).
            gross_salary: Gross salary amount.
            deductions: Total deductions.
            insurance_employee: Employee insurance contribution.
            taxable_income: Taxable income.
            pit_amount: Personal income tax.
            net_salary: Net salary (take-home).
            pdf_url: Optional PDF URL.

        Returns:
            The created draft Payslip.

        Raises:
            PayslipAlreadyExistsError: If a payslip already exists for
                this Employee and period.
        """
        try:
            payslip = await self._payslip_repo.create(
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
        except IntegrityError:
            raise PayslipAlreadyExistsError(str(employee_id), str(period_month))

        await self._audit_service.log_action(
            admin=admin,
            action_type=AuditActionType.PAYSLIP_CREATE,
            details={
                "payslip_id": str(payslip.id),
                "employee_id": str(employee_id),
                "period_month": str(period_month),
                "gross_salary": str(gross_salary),
                "net_salary": str(net_salary),
            },
        )

        return payslip

    async def update_draft(
        self,
        admin: User,
        payslip_id: UUID,
        *,
        gross_salary: Decimal | None = None,
        deductions: Decimal | None = None,
        insurance_employee: Decimal | None = None,
        taxable_income: Decimal | None = None,
        pit_amount: Decimal | None = None,
        net_salary: Decimal | None = None,
        pdf_url: str | None = None,
    ) -> Payslip:
        """Update a draft Payslip values.

        Only draft payslips can be updated. None fields are ignored.

        Args:
            admin: The admin performing the action.
            payslip_id: The UUID of the payslip to update.
            gross_salary: Optional new gross salary.
            deductions: Optional new deductions.
            insurance_employee: Optional new insurance contribution.
            taxable_income: Optional new taxable income.
            pit_amount: Optional new PIT amount.
            net_salary: Optional new net salary.
            pdf_url: Optional new PDF URL.

        Returns:
            The updated Payslip.

        Raises:
            PayslipNotFoundError: If the payslip does not exist.
            PayslipNotDraftError: If the payslip is not in draft status.
        """
        payslip = await self._payslip_repo.get_by_id(payslip_id)
        if payslip is None:
            raise PayslipNotFoundError(str(payslip_id))
        if payslip.status != PayslipStatus.DRAFT:
            raise PayslipNotDraftError(str(payslip_id))

        payslip = await self._payslip_repo.update(
            payslip_id=payslip_id,
            gross_salary=gross_salary,
            deductions=deductions,
            insurance_employee=insurance_employee,
            taxable_income=taxable_income,
            pit_amount=pit_amount,
            net_salary=net_salary,
            pdf_url=pdf_url,
        )

        # payslip should never be None here since we already fetched it
        assert payslip is not None

        await self._audit_service.log_action(
            admin=admin,
            action_type=AuditActionType.PAYSLIP_UPDATE,
            details={
                "payslip_id": str(payslip_id),
                "employee_id": str(payslip.employee_id),
                "period_month": str(payslip.period_month),
            },
        )

        return payslip

    async def publish(
        self,
        admin: User,
        payslip_id: UUID,
    ) -> Payslip:
        """Publish a draft Payslip.

        Once published, the Payslip becomes visible to the Employee
        and can no longer be modified.

        Args:
            admin: The admin performing the action.
            payslip_id: The UUID of the payslip to publish.

        Returns:
            The published Payslip.

        Raises:
            PayslipNotFoundError: If the payslip does not exist.
            PayslipAlreadyPublishedError: If already published.
        """
        payslip = await self._payslip_repo.get_by_id(payslip_id)
        if payslip is None:
            raise PayslipNotFoundError(str(payslip_id))
        if payslip.status == PayslipStatus.PUBLISHED:
            raise PayslipAlreadyPublishedError(str(payslip_id))

        payslip = await self._payslip_repo.publish(payslip_id)

        # payslip should never be None here since we already fetched it
        assert payslip is not None

        await self._audit_service.log_action(
            admin=admin,
            action_type=AuditActionType.PAYSLIP_PUBLISH,
            details={
                "payslip_id": str(payslip_id),
                "employee_id": str(payslip.employee_id),
                "period_month": str(payslip.period_month),
                "published_at": str(payslip.published_at),
            },
        )

        return payslip

    async def delete(
        self,
        admin: User,
        payslip_id: UUID,
    ) -> None:
        """Delete a draft Payslip.

        Only draft payslips can be deleted.

        Args:
            admin: The admin performing the action.
            payslip_id: The UUID of the payslip to delete.

        Raises:
            PayslipNotFoundError: If the payslip does not exist.
            PayslipNotDraftError: If the payslip is not in draft status.
        """
        payslip = await self._payslip_repo.get_by_id(payslip_id)
        if payslip is None:
            raise PayslipNotFoundError(str(payslip_id))
        if payslip.status != PayslipStatus.DRAFT:
            raise PayslipNotDraftError(str(payslip_id))

        await self._payslip_repo.delete(payslip_id)

        await self._audit_service.log_action(
            admin=admin,
            action_type=AuditActionType.PAYSLIP_DELETE,
            details={
                "payslip_id": str(payslip_id),
                "employee_id": str(payslip.employee_id),
                "period_month": str(payslip.period_month),
            },
        )

    async def list_payslips(
        self,
        admin: User,
        page: int = 1,
        page_size: int = 20,
        employee_id: UUID | None = None,
        status: PayslipStatus | None = None,
        period_month: date | None = None,
    ) -> tuple[list[Payslip], int]:
        """List payslips with optional filters.

        Args:
            admin: The admin performing the action.
            page: Page number (1-based).
            page_size: Records per page.
            employee_id: Optional employee filter.
            status: Optional status filter.
            period_month: Optional period filter.

        Returns:
            Tuple of (list of Payslip, total count).
        """
        total = await self._payslip_repo.count_all(
            employee_id=employee_id,
            status=status,
            period_month=period_month,
        )
        payslips = await self._payslip_repo.list_all(
            page=page,
            page_size=page_size,
            employee_id=employee_id,
            status=status,
            period_month=period_month,
        )
        return payslips, total

    async def get_payslip_by_id(
        self,
        admin: User,
        payslip_id: UUID,
    ) -> Payslip:
        """Get a specific payslip by ID (any status, for admin).

        Args:
            admin: The admin performing the action.
            payslip_id: The UUID of the payslip.

        Returns:
            The Payslip.

        Raises:
            PayslipNotFoundError: If the payslip does not exist.
        """
        payslip = await self._payslip_repo.get_by_id(payslip_id)
        if payslip is None:
            raise PayslipNotFoundError(str(payslip_id))
        return payslip
