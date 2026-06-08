"""Dependency injection container for the Attendance module.

Provides FastAPI dependency functions that wire together the
AttendanceSettingsService and its dependencies, following the same
module layout as other Vroom HR modules (api → application → domain →
infrastructure).
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.application.attendance_settings_service import (
    AttendanceSettingsService,
)
from src.modules.identity.container import get_db_session
from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)


async def get_organization_settings_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSettingsRepository:
    """Provide an OrganizationSettingsRepository bound to the current session.

    Args:
        session: The async database session from DI.

    Returns:
        An OrganizationSettingsRepository for the current request.
    """
    return OrganizationSettingsRepository(session=session)


async def get_attendance_settings_service(
    org_repo: OrganizationSettingsRepository = Depends(
        get_organization_settings_repository,
    ),
) -> AttendanceSettingsService:
    """Provide an AttendanceSettingsService instance.

    Args:
        org_repo: The organization settings repository from DI.

    Returns:
        An AttendanceSettingsService for the current request.
    """
    return AttendanceSettingsService(org_repo=org_repo)
