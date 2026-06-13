"""Dependency injection container for the Employee Request module.

Provides FastAPI dependency functions that wire together the overtime
and leave services with their repository.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.employee_request.application.leave_service import LeaveService
from src.modules.employee_request.application.overtime_service import OvertimeService
from src.modules.employee_request.application.review_service import (
    EmployeeRequestReviewService,
)
from src.modules.employee_request.infrastructure.employee_request_repository import (
    EmployeeRequestRepository,
)
from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.container import (
    get_audit_service,
    get_db_session,
)


async def get_employee_request_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeRequestRepository:
    """Provide an EmployeeRequestRepository bound to the current session."""
    return EmployeeRequestRepository(session=session)


async def get_overtime_service(
    repo: EmployeeRequestRepository = Depends(get_employee_request_repository),
) -> OvertimeService:
    """Provide an OvertimeService instance."""
    return OvertimeService(repo=repo)


async def get_leave_service(
    repo: EmployeeRequestRepository = Depends(get_employee_request_repository),
) -> LeaveService:
    """Provide a LeaveService instance."""
    return LeaveService(repo=repo)


async def get_employee_request_review_service(
    repo: EmployeeRequestRepository = Depends(get_employee_request_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> EmployeeRequestReviewService:
    """Provide an EmployeeRequestReviewService instance."""
    return EmployeeRequestReviewService(repo=repo, audit_service=audit_service)
