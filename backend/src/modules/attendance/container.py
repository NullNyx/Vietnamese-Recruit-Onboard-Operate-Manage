"""Dependency injection container for the Attendance & Payroll module.

Provides FastAPI dependency functions that wire together all services,
repositories, and infrastructure components using the shared async 
database session from the identity module.
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.application.attendance_service import AttendanceService
from src.modules.attendance.application.payroll_service import PayrollService
from src.modules.attendance.infrastructure.attendance_repository import AttendanceRepository
from src.modules.attendance.infrastructure.payroll_repository import PayrollRepository
from src.modules.attendance.infrastructure.settings_repository import SettingsRepository
from src.modules.identity.container import get_db_session


# ---------------------------------------------------------------------------
# Repository dependency functions
# ---------------------------------------------------------------------------

async def get_attendance_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AttendanceRepository:
    """Provide an AttendanceRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        An AttendanceRepository bound to the current session.
    """
    return AttendanceRepository(session)


async def get_settings_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SettingsRepository:
    """Provide a SettingsRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        A SettingsRepository bound to the current session.
    """
    return SettingsRepository(session)


async def get_payroll_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PayrollRepository:
    """Provide a PayrollRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        A PayrollRepository bound to the current session.
    """
    return PayrollRepository(session)


# ---------------------------------------------------------------------------
# Service dependency functions
# ---------------------------------------------------------------------------

async def get_attendance_service(
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    settings_repo: SettingsRepository = Depends(get_settings_repository),
) -> AttendanceService:
    """Provide an AttendanceService instance with all dependencies.

    Args:
        attendance_repo: The attendance repository from DI.
        settings_repo: The settings repository from DI.

    Returns:
        A fully configured AttendanceService.
    """
    return AttendanceService(
        attendance_repository=attendance_repo,
        settings_repository=settings_repo,
    )


async def get_payroll_service(
    payroll_repo: PayrollRepository = Depends(get_payroll_repository),
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    settings_repo: SettingsRepository = Depends(get_settings_repository),
) -> PayrollService:
    """Provide a PayrollService instance with all dependencies.

    Args:
        payroll_repo: The payroll repository from DI.
        attendance_repo: The attendance repository from DI.
        settings_repo: The settings repository from DI.

    Returns:
        A fully configured PayrollService.
    """
    return PayrollService(
        payroll_repository=payroll_repo,
        attendance_repository=attendance_repo,
        settings_repository=settings_repo,
    )
