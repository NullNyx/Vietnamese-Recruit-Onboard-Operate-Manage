"""FastAPI router for Employee-owned Payslip endpoints.

All employee-owned endpoints live under /api/payslips/me/ and require
an authenticated active Employee. Read-only per ADR-0012 and ADR-0016.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.modules.employee.api.dependencies import get_current_employee
from src.modules.employee.domain.entities import Employee
from src.modules.payslip.api.schemas import PayslipListResponse, PayslipResponse
from src.modules.payslip.application.payslip_service import PayslipService
from src.modules.payslip.container import get_payslip_service
from src.modules.payslip.domain.exceptions import (
    PayslipNotFoundError,
    PayslipNotPublishedError,
)

employee_payslip_router = APIRouter(
    prefix="/api/payslips",
    tags=["payslips"],
)


def _require_active_employee(
    employee: Employee | None = Depends(get_current_employee),
) -> Employee:
    """Dependency that requires an active Employee (not admin)."""
    if employee is None:
        raise HTTPException(status_code=403, detail="Only employees can access payslips")
    return employee


@employee_payslip_router.get(
    "/me",
    response_model=PayslipListResponse,
)
async def list_my_payslips(
    employee: Employee = Depends(_require_active_employee),
    service: PayslipService = Depends(get_payslip_service),
) -> PayslipListResponse:
    """List all published payslips for the authenticated employee."""
    payslips = await service.get_my_payslips(employee.id)
    return PayslipListResponse(
        payslips=[PayslipResponse.model_validate(p) for p in payslips],
    )


@employee_payslip_router.get(
    "/me/{payslip_id}",
    response_model=PayslipResponse,
)
async def get_my_payslip(
    payslip_id: UUID,
    employee: Employee = Depends(_require_active_employee),
    service: PayslipService = Depends(get_payslip_service),
) -> PayslipResponse:
    """Get a specific published payslip owned by the authenticated employee."""
    try:
        payslip = await service.get_my_payslip_by_id(
            payslip_id=payslip_id,
            employee_id=employee.id,
        )
    except PayslipNotFoundError:
        raise HTTPException(status_code=404, detail="Payslip not found")
    except PayslipNotPublishedError:
        raise HTTPException(status_code=404, detail="Payslip not found")

    return PayslipResponse.model_validate(payslip)
