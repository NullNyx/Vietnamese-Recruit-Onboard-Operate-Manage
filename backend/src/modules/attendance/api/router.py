"""FastAPI router for Attendance network configuration.

Defines the /api/attendance/settings/network endpoints for managing
the office network allowlist. All endpoints require authentication,
and write operations require HR/Admin role.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.api.schemas import (
    NetworkAddRequest,
    NetworkAllowlistResponse,
    NetworkAllowlistUpdate,
)
from src.modules.attendance.application.attendance_settings_service import (
    AttendanceSettingsService,
)
from src.modules.identity.container import get_current_user, get_db_session
from src.modules.identity.domain.entities import User, UserRole

attendance_router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def get_attendance_settings_service(
    session: AsyncSession = Depends(get_db_session),
) -> AttendanceSettingsService:
    """Provide an AttendanceSettingsService instance."""
    from src.modules.recruitment.infrastructure.org_settings_repository import (
        OrganizationSettingsRepository,
    )

    org_repo = OrganizationSettingsRepository(session=session)
    return AttendanceSettingsService(org_repo=org_repo)


def require_hr(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires HR/Admin role."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="HR/Admin access required")
    return user


def require_auth(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires authentication."""
    return user


@attendance_router.get("/settings/network", response_model=NetworkAllowlistResponse)
async def get_network_allowlist(
    user: User = Depends(require_auth),
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
    user: User = Depends(require_hr),
    service: AttendanceSettingsService = Depends(get_attendance_settings_service),
) -> NetworkAllowlistResponse:
    """Replace the entire attendance network allowlist.

    HR/Admin only.
    """
    networks = await service.set_allowed_networks(update.networks)
    return NetworkAllowlistResponse(networks=networks)


@attendance_router.post("/settings/network/add", response_model=NetworkAllowlistResponse)
async def add_to_network_allowlist(
    add_request: NetworkAddRequest,
    user: User = Depends(require_hr),
    service: AttendanceSettingsService = Depends(get_attendance_settings_service),
) -> NetworkAllowlistResponse:
    """Add one or more CIDRs to the allowlist.

    HR/Admin only.
    """
    networks = await service.add_networks(add_request.networks)
    return NetworkAllowlistResponse(networks=networks)


@attendance_router.delete(
    "/settings/network",
    response_model=NetworkAllowlistResponse,
)
async def remove_from_network_allowlist(
    cidr: str = Query(..., description="CIDR notation to remove"),
    user: User = Depends(require_hr),
    service: AttendanceSettingsService = Depends(get_attendance_settings_service),
) -> NetworkAllowlistResponse:
    """Remove a CIDR from the allowlist.

    HR/Admin only.
    """
    networks = await service.remove_network(cidr)
    return NetworkAllowlistResponse(networks=networks)
