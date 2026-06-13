"""Application service for Employee-owned Payslip read operations.

Handles listing and reading published payslips for the authenticated
Employee. No create, update, publish, or delete — those are HR-admin
concerns (separate module scope). Enforces the read-only contract from
ADR-0012 and ADR-0016.
"""

from uuid import UUID

from src.modules.payslip.domain.entities import Payslip
from src.modules.payslip.domain.exceptions import (
    PayslipNotFoundError,
)
from src.modules.payslip.infrastructure.payslip_repository import PayslipRepository


class PayslipService:
    """Service for employee-owned payslip read operations.

    All reads are scoped to the authenticated Employee and only return
    published payslips.
    """

    def __init__(self, payslip_repo: PayslipRepository) -> None:
        self._payslip_repo = payslip_repo

    async def get_my_payslips(self, employee_id: UUID) -> list[Payslip]:
        """List all published payslips for the authenticated employee.

        Args:
            employee_id: The ID of the authenticated employee.

        Returns:
            List of published Payslip entities ordered by period descending.
        """
        return await self._payslip_repo.list_by_employee(employee_id)

    async def get_my_payslip_by_id(
        self,
        payslip_id: UUID,
        employee_id: UUID,
    ) -> Payslip:
        """Get a specific published payslip owned by the authenticated employee.

        Fail-closed: single query checks both ownership AND published status.
        This avoids leaking whether a payslip exists but isn't published.

        Args:
            payslip_id: The ID of the payslip to retrieve.
            employee_id: The ID of the authenticated employee.

        Returns:
            The published Payslip.

        Raises:
            PayslipNotFoundError: If the payslip does not exist,
                is not published, or does not belong to the employee.
        """
        payslip = await self._payslip_repo.get_published_by_id_and_employee(
            payslip_id=payslip_id,
            employee_id=employee_id,
        )

        if payslip is None:
            raise PayslipNotFoundError(str(payslip_id))

        return payslip
