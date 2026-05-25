"""FastAPI router for Employee Self-Service leave endpoints.

Provides endpoints for employees to view leave balances, list their
leave requests, submit new leave requests, and cancel pending requests.
All endpoints enforce ownership via the rate-limited employee_id dependency.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.modules.self_service.api.rate_limiter import check_ess_rate_limit
from src.modules.self_service.api.schemas import (
    ESSLeaveBalanceResponse,
    ESSLeaveRequestCreate,
    ESSLeaveRequestResponse,
)
from src.modules.self_service.application.ess_leave_service import ESSLeaveService
from src.modules.self_service.container import get_ess_leave_service

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

EmployeeIdDep = Annotated[UUID, Depends(check_ess_rate_limit)]


LeaveServiceDep = Annotated[ESSLeaveService, Depends(get_ess_leave_service)]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

leave_router = APIRouter(prefix="/leave", tags=["ess-leave"])


@leave_router.get("/balances", response_model=list[ESSLeaveBalanceResponse])
async def get_leave_balances(
    employee_id: EmployeeIdDep,
    service: LeaveServiceDep,
) -> list[ESSLeaveBalanceResponse]:
    """View leave balances for the authenticated employee.

    Returns all leave type balances for the current year, including
    total_days, used_days, and remaining_days grouped by leave type.

    Requirements: 6.1, 7.1
    """
    return await service.get_balances(employee_id)


@leave_router.get("/requests", response_model=list[ESSLeaveRequestResponse])
async def get_leave_requests(
    employee_id: EmployeeIdDep,
    service: LeaveServiceDep,
) -> list[ESSLeaveRequestResponse]:
    """List all leave requests for the authenticated employee.

    Returns leave requests with status, dates, type name, and
    approval details. Only returns requests owned by the employee.

    Requirements: 6.4
    """
    return await service.get_requests(employee_id)


@leave_router.post(
    "/requests",
    response_model=ESSLeaveRequestResponse,
    status_code=201,
)
async def create_leave_request(
    data: ESSLeaveRequestCreate,
    employee_id: EmployeeIdDep,
    service: LeaveServiceDep,
) -> ESSLeaveRequestResponse:
    """Submit a new leave request.

    Validates that start_date is not in the past, end_date >= start_date,
    and sufficient leave balance exists for the requested type and days.
    The request is created with status "pending".

    Requirements: 6.1, 6.5
    """
    return await service.create_request(employee_id, data)


@leave_router.post(
    "/requests/{request_id}/cancel",
    response_model=ESSLeaveRequestResponse,
)
async def cancel_leave_request(
    request_id: UUID,
    employee_id: EmployeeIdDep,
    service: LeaveServiceDep,
) -> ESSLeaveRequestResponse:
    """Cancel a pending leave request.

    Verifies that the request belongs to the authenticated employee
    and that its current status is "pending". Only pending requests
    can be cancelled.

    Requirements: 6.5, 7.3
    """
    return await service.cancel_request(employee_id, request_id)
