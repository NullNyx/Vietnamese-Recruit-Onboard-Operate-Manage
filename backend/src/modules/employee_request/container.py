"""Dependency injection container for the Employee Request module.

Provides FastAPI dependency functions that wire together the overtime
service and its repository.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.employee_request.application.overtime_service import OvertimeService
from src.modules.employee_request.infrastructure.employee_request_repository import (
    EmployeeRequestRepository,
)
from src.modules.identity.container import get_db_session


async def get_employee_request_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeRequestRepository:
    """Provide an EmployeeRequestRepository bound to the current session.

    Args:
        session: The async database session from DI.

    Returns:
        An EmployeeRequestRepository for the current request.
    """
    return EmployeeRequestRepository(session=session)


async def get_overtime_service(
    repo: EmployeeRequestRepository = Depends(get_employee_request_repository),
) -> OvertimeService:
    """Provide an OvertimeService instance.

    Args:
        repo: The employee request repository from DI.

    Returns:
        An OvertimeService for the current request.
    """
    return OvertimeService(repo=repo)
