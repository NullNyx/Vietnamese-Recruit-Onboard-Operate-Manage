"""FastAPI router for Employee Request overtime endpoints.

All endpoints live under /api/employee-requests/me/ and require
an authenticated Employee (not just a User).  The employee is
resolved from the JWT token via ``get_current_employee``.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.modules.employee.api.dependencies import get_current_employee
from src.modules.employee.domain.entities import Employee
from src.modules.employee_request.api.schemas import (
    OvertimeCancelRequest,
    OvertimeCancelResponse,
    OvertimeCreateRequest,
    OvertimeCreateResponse,
    OvertimeListResponse,
    OvertimeResponse,
)
from src.modules.employee_request.application.overtime_service import OvertimeService
from src.modules.employee_request.container import get_overtime_service
from src.modules.employee_request.domain.exceptions import (
    OvertimeEndBeforeStartError,
    OvertimeOverlapError,
    RequestNotCancellableError,
    RequestNotFoundError,
    RequestNotOwnedByEmployeeError,
)

employee_request_router = APIRouter(
    prefix="/api/employee-requests",
    tags=["employee-requests"],
)


def _require_active_employee(
    employee: Employee | None = Depends(get_current_employee),
) -> Employee:
    """Dependency that requires an active Employee (not admin)."""
    if employee is None:
        raise HTTPException(status_code=403, detail="Only employees can submit requests")
    return employee


@employee_request_router.post(
    "/me/overtime",
    response_model=OvertimeCreateResponse,
    status_code=201,
)
async def create_overtime(
    body: OvertimeCreateRequest,
    employee: Employee = Depends(_require_active_employee),
    service: OvertimeService = Depends(get_overtime_service),
) -> OvertimeCreateResponse:
    """Create a new overtime request.

    The authenticated employee becomes the owner of the request.
    Duration is derived from start/end times, not user-entered.
    """
    try:
        request = await service.create_overtime(
            employee_id=employee.id,
            work_date=body.work_date,
            start_time=body.start_time,
            end_time=body.end_time,
            reason=body.reason,
            project_or_task=body.project_or_task,
        )
    except OvertimeEndBeforeStartError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except OvertimeOverlapError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return OvertimeCreateResponse(
        message="Overtime request submitted",
        request=OvertimeResponse.model_validate(request),
    )


@employee_request_router.post(
    "/me/overtime/{request_id}/cancel",
    response_model=OvertimeCancelResponse,
)
async def cancel_overtime(
    request_id: UUID,
    body: OvertimeCancelRequest,
    employee: Employee = Depends(_require_active_employee),
    service: OvertimeService = Depends(get_overtime_service),
) -> OvertimeCancelResponse:
    """Cancel own submitted overtime request.

    Only the owning employee can cancel, and only if status is SUBMITTED.
    """
    try:
        request = await service.cancel_overtime(
            request_id=request_id,
            employee_id=employee.id,
            cancellation_reason=body.cancellation_reason,
        )
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except RequestNotOwnedByEmployeeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except RequestNotCancellableError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return OvertimeCancelResponse(
        message="Overtime request cancelled",
        request=OvertimeResponse.model_validate(request),
    )


@employee_request_router.get(
    "/me/overtime",
    response_model=OvertimeListResponse,
)
async def list_my_overtime(
    employee: Employee = Depends(_require_active_employee),
    service: OvertimeService = Depends(get_overtime_service),
) -> OvertimeListResponse:
    """List all overtime requests for the current employee."""
    requests = await service.list_my_overtime(employee_id=employee.id)
    return OvertimeListResponse(
        requests=[OvertimeResponse.model_validate(r) for r in requests],
    )
