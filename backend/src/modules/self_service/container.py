"""Dependency injection container for the Employee Self-Service module.

Provides FastAPI dependency functions that wire together ESS services
with existing module dependencies (EmployeeService, AttendanceService,
LeaveService, OvertimeService) and infrastructure (Redis for rate limiting).
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.infrastructure.attendance_repository import (
    AttendanceRepository,
)
from src.modules.attendance.infrastructure.leave_repository import (
    LeaveBalanceRepository,
    LeaveRequestRepository,
    LeaveTypeRepository,
)
from src.modules.attendance.infrastructure.schedule_repository import (
    ScheduleRepository,
)
from src.modules.employee.infrastructure.department_repository import (
    DepartmentRepository,
)
from src.modules.employee.infrastructure.employee_repository import (
    EmployeeRepository,
)
from src.modules.employee.infrastructure.position_repository import (
    PositionRepository,
)
from src.modules.identity.container import get_db_session
from src.modules.self_service.application.ess_attendance_service import (
    ESSAttendanceService,
)
from src.modules.self_service.application.ess_dashboard_service import (
    ESSDashboardService,
)
from src.modules.self_service.application.ess_leave_service import (
    ESSLeaveService,
)
from src.modules.self_service.application.ess_overtime_service import (
    ESSOvertimeService,
)
from src.modules.self_service.application.ess_profile_service import (
    ESSProfileService,
)


# ---------------------------------------------------------------------------
# Repository dependency functions
# ---------------------------------------------------------------------------


async def get_employee_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeRepository:
    """Provide an EmployeeRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        An EmployeeRepository bound to the current session.
    """
    return EmployeeRepository(session)


async def get_department_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DepartmentRepository:
    """Provide a DepartmentRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        A DepartmentRepository bound to the current session.
    """
    return DepartmentRepository(session)


async def get_position_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PositionRepository:
    """Provide a PositionRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        A PositionRepository bound to the current session.
    """
    return PositionRepository(session)


async def get_attendance_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AttendanceRepository:
    """Provide an AttendanceRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        An AttendanceRepository bound to the current session.
    """
    return AttendanceRepository(session)


async def get_schedule_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ScheduleRepository:
    """Provide a ScheduleRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        A ScheduleRepository bound to the current session.
    """
    return ScheduleRepository(session)


async def get_leave_balance_repository(
    session: AsyncSession = Depends(get_db_session),
) -> LeaveBalanceRepository:
    """Provide a LeaveBalanceRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        A LeaveBalanceRepository bound to the current session.
    """
    return LeaveBalanceRepository(session)


async def get_leave_request_repository(
    session: AsyncSession = Depends(get_db_session),
) -> LeaveRequestRepository:
    """Provide a LeaveRequestRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        A LeaveRequestRepository bound to the current session.
    """
    return LeaveRequestRepository(session)


async def get_leave_type_repository(
    session: AsyncSession = Depends(get_db_session),
) -> LeaveTypeRepository:
    """Provide a LeaveTypeRepository instance for ESS.

    Args:
        session: The async database session from DI.

    Returns:
        A LeaveTypeRepository bound to the current session.
    """
    return LeaveTypeRepository(session)


# ---------------------------------------------------------------------------
# ESS Service dependency functions
# ---------------------------------------------------------------------------


async def get_ess_profile_service(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    department_repo: DepartmentRepository = Depends(get_department_repository),
    position_repo: PositionRepository = Depends(get_position_repository),
) -> ESSProfileService:
    """Provide an ESSProfileService instance with all dependencies.

    Args:
        employee_repo: Repository for employee data access.
        department_repo: Repository for department lookups.
        position_repo: Repository for position lookups.

    Returns:
        A fully configured ESSProfileService.
    """
    return ESSProfileService(
        employee_repository=employee_repo,
        department_repository=department_repo,
        position_repository=position_repo,
    )


async def get_ess_attendance_service(
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    schedule_repo: ScheduleRepository = Depends(get_schedule_repository),
) -> ESSAttendanceService:
    """Provide an ESSAttendanceService instance with all dependencies.

    Args:
        attendance_repo: Repository for attendance record persistence.
        schedule_repo: Repository for work schedule lookups.

    Returns:
        A fully configured ESSAttendanceService.
    """
    return ESSAttendanceService(
        attendance_repo=attendance_repo,
        schedule_repo=schedule_repo,
    )


async def get_ess_leave_service(
    balance_repo: LeaveBalanceRepository = Depends(get_leave_balance_repository),
    request_repo: LeaveRequestRepository = Depends(get_leave_request_repository),
    type_repo: LeaveTypeRepository = Depends(get_leave_type_repository),
    session: AsyncSession = Depends(get_db_session),
) -> ESSLeaveService:
    """Provide an ESSLeaveService instance with all dependencies.

    Args:
        balance_repo: Repository for leave balance queries.
        request_repo: Repository for leave request CRUD.
        type_repo: Repository for leave type lookups.
        session: Database session for transaction management.

    Returns:
        A fully configured ESSLeaveService.
    """
    return ESSLeaveService(
        balance_repo=balance_repo,
        request_repo=request_repo,
        type_repo=type_repo,
        session=session,
    )


async def get_ess_overtime_service(
    session: AsyncSession = Depends(get_db_session),
) -> ESSOvertimeService:
    """Provide an ESSOvertimeService instance.

    Args:
        session: Async database session for queries and mutations.

    Returns:
        A fully configured ESSOvertimeService.
    """
    return ESSOvertimeService(session=session)


async def get_ess_dashboard_service(
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    session: AsyncSession = Depends(get_db_session),
) -> ESSDashboardService:
    """Provide an ESSDashboardService instance with all dependencies.

    Args:
        attendance_repo: Repository for attendance record queries.
        session: Async database session for direct queries.

    Returns:
        A fully configured ESSDashboardService.
    """
    return ESSDashboardService(
        attendance_repo=attendance_repo,
        session=session,
    )
