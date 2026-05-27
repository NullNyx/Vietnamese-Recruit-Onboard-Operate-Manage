"""FastAPI router for Employee Self-Service overtime endpoints.

Provides endpoints for employees to list, create, and cancel their own
overtime requests. All endpoints enforce ownership via the rate-limited
employee dependency and delegate to ESSOvertimeService.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.modules.self_service.api.rate_limiter import check_ess_rate_limit
from src.modules.self_service.api.schemas import (
    ESSOvertimeRequestCreate,
    ESSOvertimeRequestResponse,
)
from src.modules.self_service.application.ess_overtime_service import ESSOvertimeService
from src.modules.self_service.container import get_ess_overtime_service

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

EmployeeIdDep = Annotated[UUID, Depends(check_ess_rate_limit)]


OvertimeServiceDep = Annotated[ESSOvertimeService, Depends(get_ess_overtime_service)]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

overtime_router = APIRouter(prefix="/overtime", tags=["ess-overtime"])


@overtime_router.get("/requests", response_model=list[ESSOvertimeRequestResponse])
async def list_overtime_requests(
    employee_id: EmployeeIdDep,
    service: OvertimeServiceDep,
) -> list[ESSOvertimeRequestResponse]:
    """List all overtime requests for the authenticated employee.

    Returns overtime requests ordered by creation date descending.
    """
    requests = await service.get_requests(employee_id)
    return [ESSOvertimeRequestResponse.model_validate(r) for r in requests]


@overtime_router.post(
    "/requests", response_model=ESSOvertimeRequestResponse, status_code=201
)
async def create_overtime_request(
    body: ESSOvertimeRequestCreate,
    employee_id: EmployeeIdDep,
    service: OvertimeServiceDep,
) -> ESSOvertimeRequestResponse:
    """Submit a new overtime request for the authenticated employee.

    Validates that work_date is not in the past and planned_hours
    is between 0.5 and 4.0.
    """
    request = await service.create_request(employee_id, body)
    return ESSOvertimeRequestResponse.model_validate(request)


@overtime_router.post(
    "/requests/{request_id}/cancel", response_model=ESSOvertimeRequestResponse
)
async def cancel_overtime_request(
    request_id: UUID,
    employee_id: EmployeeIdDep,
    service: OvertimeServiceDep,
) -> ESSOvertimeRequestResponse:
    """Cancel a pending overtime request owned by the authenticated employee.

    Only requests with status "pending" can be cancelled. Returns 403 if
    the request belongs to another employee, 409 if not in pending status.
    """
    request = await service.cancel_request(employee_id, request_id)
    return ESSOvertimeRequestResponse.model_validate(request)
