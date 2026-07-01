"""Dependency injection container for the Employee Management module.

Provides FastAPI dependency functions that wire together all services,
repositories, and infrastructure components (MinIO client) using the
shared async database session from the identity module.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.employee.application.department_service import DepartmentService
from src.modules.employee.application.contract_amendment_service import (
    ContractAmendmentService,
)
from src.modules.employee.application.contract_service import ContractService
from src.modules.employee.application.contract_template_service import (
    ContractTemplateService,
)
from src.modules.employee.application.document_service import DocumentService
from src.modules.employee.application.employment_event_service import (
    EmploymentEventService,
)
from src.modules.employee.application.import_service import ImportService
from src.modules.employee.application.position_service import PositionService
from src.modules.employee.infrastructure.config import EmployeeSettings
from src.modules.employee.infrastructure.contract_amendment_repository import (
    ContractAmendmentRepository,
)
from src.modules.employee.infrastructure.contract_repository import ContractRepository
from src.modules.employee.infrastructure.contract_template_repository import (
    ContractTemplateRepository,
)
from src.modules.employee.infrastructure.department_repository import DepartmentRepository
from src.modules.employee.infrastructure.document_repository import DocumentRepository
from src.modules.employee.infrastructure.employment_event_repository import (
    EmploymentEventRepository,
)
from src.modules.employee.infrastructure.employee_repository import EmployeeRepository
from src.modules.employee.infrastructure.minio_client import MinIOClient
from src.modules.employee.infrastructure.position_repository import PositionRepository
from src.modules.identity.container import get_db_session

# ---------------------------------------------------------------------------
# Singleton infrastructure components
# ---------------------------------------------------------------------------


@lru_cache
def get_employee_settings() -> EmployeeSettings:
    """Load and cache EmployeeSettings from environment variables.

    Returns:
        The EmployeeSettings singleton loaded from EMPLOYEE_* env vars.
    """
    return EmployeeSettings()


@lru_cache
def get_minio_client() -> MinIOClient:
    """Create and cache the MinIOClient singleton.

    Returns:
        A MinIOClient configured with employee module settings.
    """
    settings = get_employee_settings()
    return MinIOClient(settings)


# ---------------------------------------------------------------------------
# Repository dependency functions
# ---------------------------------------------------------------------------


async def get_employee_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeRepository:
    """Provide an EmployeeRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        An EmployeeRepository bound to the current session.
    """
    return EmployeeRepository(session)


async def get_department_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DepartmentRepository:
    """Provide a DepartmentRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        A DepartmentRepository bound to the current session.
    """
    return DepartmentRepository(session)


async def get_position_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PositionRepository:
    """Provide a PositionRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        A PositionRepository bound to the current session.
    """
    return PositionRepository(session)


async def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRepository:
    """Provide a DocumentRepository instance.

    Args:
        session: The async database session from DI.

    Returns:
        A DocumentRepository bound to the current session.
    """
    return DocumentRepository(session)

async def get_employment_event_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmploymentEventRepository:
    """Provide an EmploymentEventRepository instance."""
    return EmploymentEventRepository(session)

async def get_contract_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ContractRepository:
    """Provide a ContractRepository instance."""
    return ContractRepository(session)

async def get_contract_template_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ContractTemplateRepository:
    """Provide a ContractTemplateRepository instance."""
    return ContractTemplateRepository(session)

async def get_contract_amendment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ContractAmendmentRepository:
    """Provide a ContractAmendmentRepository instance."""
    return ContractAmendmentRepository(session)

async def get_employment_event_service(
    event_repo: EmploymentEventRepository = Depends(get_employment_event_repository),
) -> EmploymentEventService:
    """Provide an EmploymentEventService instance."""
    return EmploymentEventService(event_repo)

async def get_contract_service(
    contract_repo: ContractRepository = Depends(get_contract_repository),
    event_service: EmploymentEventService = Depends(get_employment_event_service),
) -> ContractService:
    """Provide a ContractService instance."""
    return ContractService(contract_repo=contract_repo, event_service=event_service)

async def get_contract_template_service(
    template_repo: ContractTemplateRepository = Depends(get_contract_template_repository),
) -> ContractTemplateService:
    """Provide a ContractTemplateService instance."""
    return ContractTemplateService(template_repo=template_repo)

async def get_contract_amendment_service(
    amendment_repo: ContractAmendmentRepository = Depends(get_contract_amendment_repository),
) -> ContractAmendmentService:
    """Provide a ContractAmendmentService instance."""
    return ContractAmendmentService(amendment_repo=amendment_repo)


# ---------------------------------------------------------------------------
# Service dependency functions
# ---------------------------------------------------------------------------


async def get_employee_service(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    department_repo: DepartmentRepository = Depends(get_department_repository),
    position_repo: PositionRepository = Depends(get_position_repository),
    event_service: EmploymentEventService = Depends(get_employment_event_service),
) -> EmployeeService:
    """Provide an EmployeeService instance with all dependencies.

    Args:
        employee_repo: The employee repository from DI.
        department_repo: The department repository from DI.
        position_repo: The position repository from DI.

    Returns:
        A fully configured EmployeeService.
    """
    return EmployeeService(
        employee_repository=employee_repo,
        department_repository=department_repo,
        position_repository=position_repo,
        event_service=event_service,
    )


async def get_department_service(
    department_repo: DepartmentRepository = Depends(get_department_repository),
) -> DepartmentService:
    """Provide a DepartmentService instance.

    Args:
        department_repo: The department repository from DI.

    Returns:
        A DepartmentService configured with the department repository.
    """
    return DepartmentService(department_repository=department_repo)


async def get_position_service(
    position_repo: PositionRepository = Depends(get_position_repository),
) -> PositionService:
    """Provide a PositionService instance.

    Args:
        position_repo: The position repository from DI.

    Returns:
        A PositionService configured with the position repository.
    """
    return PositionService(position_repository=position_repo)


async def get_import_service(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    department_repo: DepartmentRepository = Depends(get_department_repository),
    position_repo: PositionRepository = Depends(get_position_repository),
) -> ImportService:
    """Provide an ImportService instance with all dependencies.

    Args:
        employee_repo: The employee repository from DI.
        department_repo: The department repository from DI.
        position_repo: The position repository from DI.

    Returns:
        A fully configured ImportService.
    """
    return ImportService(
        employee_repository=employee_repo,
        department_repository=department_repo,
        position_repository=position_repo,
    )


async def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    event_service: EmploymentEventService = Depends(get_employment_event_service),
) -> DocumentService:
    return DocumentService(
        document_repository=document_repo,
        employee_repository=employee_repo,
        minio_client=get_minio_client(),
        settings=get_employee_settings(),
        event_service=event_service,
    )

async def get_contract_amendment_service(
    amendment_repo: ContractAmendmentRepository = Depends(get_contract_amendment_repository),
) -> ContractAmendmentService:
    return ContractAmendmentService(amendment_repo)
