"""Dependency injection container for the Attendance module.

Provides FastAPI dependency functions that wire together all services,
repositories, and infrastructure components using async database sessions.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.application.attendance_service import AttendanceService
from src.modules.attendance.application.attendance_settings_service import (
    AttendanceSettingsService,
)
from src.modules.attendance.infrastructure.attendance_record_repository import (
    AttendanceRecordRepository,
)
from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.container import get_db_session
from src.modules.identity.infrastructure.audit_log_repository import (
    AuditLogRepository,
)
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


async def get_attendance_record_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AttendanceRecordRepository:
    """Provide an AttendanceRecordRepository bound to the current session.

    Args:
        session: The async database session from DI.

    Returns:
        An AttendanceRecordRepository for the current request.
    """
    return AttendanceRecordRepository(session=session)


async def get_attendance_service(
    attendance_repo: AttendanceRecordRepository = Depends(
        get_attendance_record_repository,
    ),
    org_repo: OrganizationSettingsRepository = Depends(
        get_organization_settings_repository,
    ),
    settings_service: AttendanceSettingsService = Depends(
        get_attendance_settings_service,
    ),
) -> AttendanceService:
    """Provide an AttendanceService instance.

    Args:
        attendance_repo: The attendance record repository.
        org_repo: The organization settings repository.
        settings_service: The attendance settings service.

    Returns:
        An AttendanceService for the current request.
    """
    return AttendanceService(
        attendance_repo=attendance_repo,
        org_settings_repo=org_repo,
        settings_service=settings_service,
    )


async def get_attendance_audit_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuditService:
    """Provide an AuditService for attendance admin actions.

    Args:
        session: The async database session from DI.

    Returns:
        An AuditService bound to the current session.
    """
    repository = AuditLogRepository(session)
    return AuditService(repository=repository)
