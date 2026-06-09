"""FastAPI router for Attendance network configuration.

Defines the /api/attendance/settings/network endpoints for managing
the office network allowlist. All endpoints require authentication,
and write operations require HR/Admin role. Every admin write action
is recorded in the audit log.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.modules.attendance.api.schemas import (
    NetworkAddRequest,
    NetworkAllowlistResponse,
    NetworkAllowlistUpdate,
)
from src.modules.attendance.application.attendance_settings_service import (
    AttendanceSettingsService,
)
from src.modules.attendance.container import (
    get_attendance_audit_service,
    get_attendance_settings_service,
)
from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.container import get_current_user
from src.modules.identity.domain.entities import AuditActionType, User, UserRole
from src.modules.identity.domain.exceptions import AccessDeniedError

attendance_router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def _require_hr(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires HR/Admin role."""
    if user.role != UserRole.ADMIN:
        raise AccessDeniedError()
    return user


@attendance_router.get("/settings/network", response_model=NetworkAllowlistResponse)
async def get_network_allowlist(
    user: User = Depends(get_current_user),
    service: AttendanceSettingsService = Depends(get_attendance_settings_service),
) -> NetworkAllowlistResponse:
    """Get the current attendance network allowlist.

    HR/Admin can view the full allowlist. Other authenticated users
    can also view (for transparency).
    """
    networks = await service.get_allowed_networks()
    return NetworkAllowlistResponse(networks=networks)


@attendance_router.put("/settings/network", response_model=NetworkAllowlistResponse)
async def update_network_allowlist(
    update: NetworkAllowlistUpdate,
    user: User = Depends(_require_hr),
    service: AttendanceSettingsService = Depends(get_attendance_settings_service),
    audit_service: AuditService = Depends(get_attendance_audit_service),
) -> NetworkAllowlistResponse:
    """Replace the entire attendance network allowlist.

    HR/Admin only. Audit-logged.
    """
    networks = await service.set_allowed_networks(update.networks)
    await audit_service.log_action(
        admin=user,
        action_type=AuditActionType.ATTENDANCE_NETWORK_UPDATE,
        details={"networks": networks, "count": len(networks)},
    )
    return NetworkAllowlistResponse(networks=networks)


@attendance_router.post("/settings/network/add", response_model=NetworkAllowlistResponse)
async def add_to_network_allowlist(
    add_request: NetworkAddRequest,
    user: User = Depends(_require_hr),
    service: AttendanceSettingsService = Depends(get_attendance_settings_service),
    audit_service: AuditService = Depends(get_attendance_audit_service),
) -> NetworkAllowlistResponse:
    """Add one or more CIDRs to the allowlist.

    HR/Admin only. Audit-logged.
    """
    networks = await service.add_networks(add_request.networks)
    await audit_service.log_action(
        admin=user,
        action_type=AuditActionType.ATTENDANCE_NETWORK_ADD,
        details={"added": add_request.networks, "total": len(networks)},
    )
    return NetworkAllowlistResponse(networks=networks)


@attendance_router.delete(
    "/settings/network",
    response_model=NetworkAllowlistResponse,
)
async def remove_from_network_allowlist(
    cidr: str = Query(..., description="CIDR notation to remove"),
    user: User = Depends(_require_hr),
    service: AttendanceSettingsService = Depends(get_attendance_settings_service),
    audit_service: AuditService = Depends(get_attendance_audit_service),
) -> NetworkAllowlistResponse:
    """Remove a CIDR from the allowlist.

    HR/Admin only. Audit-logged.
    """
    networks = await service.remove_network(cidr)
    await audit_service.log_action(
        admin=user,
        action_type=AuditActionType.ATTENDANCE_NETWORK_REMOVE,
        details={"removed": cidr, "remaining": len(networks)},
    )
    return NetworkAllowlistResponse(networks=networks)


# Employee-owned attendance endpoints

from fastapi import Request

from src.modules.attendance.api.schemas import (
    AttendanceRecordResponse,
    CheckInResponse,
    CheckOutResponse,
)
from src.modules.attendance.application.attendance_service import AttendanceService
from src.modules.attendance.container import get_attendance_service
from src.modules.identity.container import get_current_employee_id


async def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def _require_employee(user_employee_id: UUID | None = Depends(get_current_employee_id)) -> UUID:
    """Dependency that requires a linked employee_id.

    Raises ValueError if no employee is linked to the current user.
    """
    if user_employee_id is None:
        raise ValueError("Employee profile required for this action")
    return user_employee_id


@attendance_router.post("/me/check-in", response_model=CheckInResponse)
async def check_in(
    request: Request,
    employee_id: UUID = Depends(_require_employee),
    service: AttendanceService = Depends(get_attendance_service),
) -> CheckInResponse:
    """Check in for today from office network.

    Idempotent: returns existing record if already checked in.
    Requires employee profile linked to user account.
    """
    client_ip = await get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    record = await service.check_in(
        employee_id=employee_id,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    return CheckInResponse(
        message="Checked in successfully",
        record=AttendanceRecordResponse.model_validate(record),
    )


@attendance_router.post("/me/check-out", response_model=CheckOutResponse)
async def check_out(
    request: Request,
    employee_id: UUID = Depends(_require_employee),
    service: AttendanceService = Depends(get_attendance_service),
) -> CheckOutResponse:
    """Check out for today from office network.

    Idempotent: returns existing record if already checked out.
    Requires check-in first.
    Requires employee profile linked to user account.
    """
    client_ip = await get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    record = await service.check_out(
        employee_id=employee_id,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    return CheckOutResponse(
        message="Checked out successfully",
        record=AttendanceRecordResponse.model_validate(record),
    )


@attendance_router.get("/me/today", response_model=AttendanceRecordResponse | None)
async def get_today_attendance(
    employee_id: UUID = Depends(_require_employee),
    service: AttendanceService = Depends(get_attendance_service),
) -> AttendanceRecordResponse | None:
    """Get today's attendance record for the current employee."""
    record = await service.get_today(employee_id)
    if record is None:
        return None
    return AttendanceRecordResponse.model_validate(record)
