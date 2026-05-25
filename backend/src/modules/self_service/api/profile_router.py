"""Profile router for Employee Self-Service endpoints.

Provides GET and PATCH endpoints for employees to view and update
their own profile data. Uses rate limiting and authentication via
the check_ess_rate_limit dependency.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.modules.self_service.api.rate_limiter import check_ess_rate_limit
from src.modules.self_service.api.schemas import ESSProfileResponse, ESSProfileUpdateRequest
from src.modules.self_service.application.ess_profile_service import ESSProfileService
from src.modules.self_service.container import get_ess_profile_service

profile_router = APIRouter(tags=["ess-profile"])


@profile_router.get("/profile", response_model=ESSProfileResponse)
async def get_profile(
    employee_id: UUID = Depends(check_ess_rate_limit),
    service: ESSProfileService = Depends(get_ess_profile_service),
) -> ESSProfileResponse:
    """Return the authenticated employee's profile with masked sensitive fields.

    Retrieves the employee record, resolves department and position names,
    and masks id_number and tax_code fields.

    Args:
        employee_id: The authenticated employee's UUID (from rate-limited auth).
        service: The ESS profile service instance.

    Returns:
        The employee's profile response with masked sensitive data.
    """
    return await service.get_profile(employee_id)


@profile_router.patch("/profile", response_model=ESSProfileResponse)
async def update_profile(
    data: ESSProfileUpdateRequest,
    employee_id: UUID = Depends(check_ess_rate_limit),
    service: ESSProfileService = Depends(get_ess_profile_service),
) -> ESSProfileResponse:
    """Update allowed profile fields for the authenticated employee.

    Only phone, address, and emergency_contact may be modified.
    Attempts to modify restricted fields result in a 403 response.

    Args:
        data: The validated update request with allowed fields only.
        employee_id: The authenticated employee's UUID (from rate-limited auth).
        service: The ESS profile service instance.

    Returns:
        The updated employee profile response.
    """
    return await service.update_profile(employee_id, data)
