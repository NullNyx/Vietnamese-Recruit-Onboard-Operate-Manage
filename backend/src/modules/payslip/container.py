"""Dependency injection container for the Payslip module.

Provides FastAPI dependency functions that wire together services and
repositories using the shared async database session.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.container import get_db_session
from src.modules.identity.infrastructure.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.payslip.application.payslip_hr_service import PayslipHRService
from src.modules.payslip.application.payslip_service import PayslipService
from src.modules.payslip.infrastructure.payslip_repository import PayslipRepository


async def get_payslip_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PayslipRepository:
    """Provide a PayslipRepository bound to the current session.

    Args:
        session: The async database session from DI.

    Returns:
        A PayslipRepository for the current request.
    """
    return PayslipRepository(session)


async def get_audit_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuditService:
    """Provide an AuditService instance.

    Args:
        session: The async database session from DI.

    Returns:
        An AuditService for the current request.
    """
    return AuditService(repository=AuditLogRepository(session))


async def get_payslip_service(
    payslip_repo: PayslipRepository = Depends(get_payslip_repository),
) -> PayslipService:
    """Provide a PayslipService instance.

    Args:
        payslip_repo: The payslip repository from DI.

    Returns:
        A PayslipService for the current request.
    """
    return PayslipService(payslip_repo=payslip_repo)


async def get_payslip_hr_service(
    payslip_repo: PayslipRepository = Depends(get_payslip_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> PayslipHRService:
    """Provide a PayslipHRService instance.

    Args:
        payslip_repo: The payslip repository from DI.
        audit_service: The audit service from DI.

    Returns:
        A PayslipHRService for the current request.
    """
    return PayslipHRService(
        payslip_repo=payslip_repo,
        audit_service=audit_service,
    )
