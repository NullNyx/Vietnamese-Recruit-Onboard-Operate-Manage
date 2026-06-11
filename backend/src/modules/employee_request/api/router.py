"""FastAPI router for Employee Request endpoints.

All employee-owned endpoints live under /api/employee-requests/me/ and
require an authenticated Employee.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.modules.employee.api.dependencies import get_current_employee
from src.modules.employee.domain.entities import Employee
from src.modules.employee_request.api.schemas import (
    EmployeeRequestListItem,
    EmployeeRequestListResponse,
    LeaveCancelRequest,
    LeaveCancelResponse,
    LeaveCreateRequest,
    LeaveCreateResponse,
    LeaveListResponse,
    LeaveResponse,
    OvertimeCancelRequest,
    OvertimeCancelResponse,
    OvertimeCreateRequest,
    OvertimeCreateResponse,
    OvertimeListResponse,
    OvertimeResponse,
)
from src.modules.employee_request.application.leave_service import LeaveService
from src.modules.employee_request.application.overtime_service import OvertimeService
from src.modules.employee_request.container import get_leave_service, get_overtime_service
from src.modules.employee_request.domain.exceptions import (
    LeaveEndBeforeStartError,
    LeaveOverlapError,
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


# ---------------------------------------------------------------------------
# Overtime endpoints
# ---------------------------------------------------------------------------


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
    """Create a new overtime request."""
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
    """Cancel own submitted overtime request."""
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


# ---------------------------------------------------------------------------
# Leave endpoints
# ---------------------------------------------------------------------------


@employee_request_router.post(
    "/me/leave",
    response_model=LeaveCreateResponse,
    status_code=201,
)
async def create_leave(
    body: LeaveCreateRequest,
    employee: Employee = Depends(_require_active_employee),
    service: LeaveService = Depends(get_leave_service),
) -> LeaveCreateResponse:
    """Create a new leave request."""
    try:
        from src.modules.employee_request.domain.enums import LeaveType

        request = await service.create_leave(
            employee_id=employee.id,
            leave_type=LeaveType(body.leave_type),
            start_date=body.start_date,
            end_date=body.end_date,
            reason=body.reason,
        )
    except LeaveEndBeforeStartError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except LeaveOverlapError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return LeaveCreateResponse(
        message="Leave request submitted",
        request=LeaveResponse.model_validate(request),
    )


@employee_request_router.post(
    "/me/leave/{request_id}/cancel",
    response_model=LeaveCancelResponse,
)
async def cancel_leave(
    request_id: UUID,
    body: LeaveCancelRequest,
    employee: Employee = Depends(_require_active_employee),
    service: LeaveService = Depends(get_leave_service),
) -> LeaveCancelResponse:
    """Cancel own submitted leave request."""
    try:
        request = await service.cancel_leave(
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

    return LeaveCancelResponse(
        message="Leave request cancelled",
        request=LeaveResponse.model_validate(request),
    )


@employee_request_router.get(
    "/me/leave",
    response_model=LeaveListResponse,
)
async def list_my_leaves(
    employee: Employee = Depends(_require_active_employee),
    service: LeaveService = Depends(get_leave_service),
) -> LeaveListResponse:
    """List all leave requests for the current employee."""
    requests = await service.list_my_leaves(employee_id=employee.id)
    return LeaveListResponse(
        requests=[LeaveResponse.model_validate(r) for r in requests],
    )


@employee_request_router.get(
    "/me",
    response_model=EmployeeRequestListResponse,
)
async def list_my_requests(
    employee: Employee = Depends(_require_active_employee),
    overtime_service: OvertimeService = Depends(get_overtime_service),
    leave_service: LeaveService = Depends(get_leave_service),
) -> EmployeeRequestListResponse:
    """List all employee requests (overtime + leave) for the current employee."""
    overtime = await overtime_service.list_my_overtime(employee_id=employee.id)
    leaves = await leave_service.list_my_leaves(employee_id=employee.id)

    all_requests = list(overtime) + list(leaves)
    all_requests.sort(key=lambda r: r.submitted_at or r.created_at, reverse=True)

    return EmployeeRequestListResponse(
        requests=[EmployeeRequestListItem.model_validate(r) for r in all_requests],
    )
