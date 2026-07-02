"""FastAPI router for the Employee Management module.

Defines the /api/employees/*, /api/departments/*, /api/positions/*,
and /api/documents/* endpoints for employee CRUD, department/position
management, Excel import, and document vault operations.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response

from src.modules.employee.api.dependencies import CurrentUserEmployee
from src.modules.employee.api.schemas import (
    ContractAmendmentCreate,
    ContractAmendmentResponse,
    ContractCreate,
    ContractRenewRequest,
    ContractResponse,
    ContractSignRequest,
    ContractTemplateCreate,
    ContractTemplateResponse,
    ContractTemplateUpdate,
    ContractUpdate,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    DocumentRejectRequest,
    DocumentResponse,
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeStatusChangeRequest,
    EmployeeUpdate,
    EmploymentEventResponse,
    ImportResult,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
    PromoteCandidateRequest,
)
from src.modules.employee.application.contract_amendment_service import (
    ContractAmendmentService,
)
from src.modules.employee.application.contract_service import ContractService
from src.modules.employee.application.contract_template_service import (
    ContractTemplateService,
)
from src.modules.employee.application.department_service import DepartmentService
from src.modules.employee.application.document_service import DocumentService
from src.modules.employee.application.employee_service import EmployeeService
from src.modules.employee.application.employment_event_service import (
    EmploymentEventService,
)
from src.modules.employee.application.import_service import ImportService
from src.modules.employee.application.position_service import PositionService
from src.modules.employee.container import (
    get_contract_amendment_service,
    get_contract_service,
    get_contract_template_service,
    get_department_service,
    get_document_service,
    get_employee_service,
    get_employment_event_service,
    get_import_service,
    get_position_service,
)
from src.modules.identity.api.admin_router import require_admin
from src.modules.identity.container import get_current_user
from src.modules.identity.domain.entities import User

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------

CurrentUserDep = Annotated[User, Depends(get_current_user)]
AdminUserDep = Annotated[User, Depends(require_admin)]
EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]
DepartmentServiceDep = Annotated[DepartmentService, Depends(get_department_service)]
PositionServiceDep = Annotated[PositionService, Depends(get_position_service)]
ImportServiceDep = Annotated[ImportService, Depends(get_import_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
ContractServiceDep = Annotated[ContractService, Depends(get_contract_service)]
ContractTemplateServiceDep = Annotated[ContractTemplateService, Depends(get_contract_template_service)]
ContractAmendmentServiceDep = Annotated[ContractAmendmentService, Depends(get_contract_amendment_service)]
EmploymentEventServiceDep = Annotated[EmploymentEventService, Depends(get_employment_event_service)]

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

router = APIRouter(tags=["employees"])

employee_router = APIRouter(prefix="/api/employees", tags=["employees"])
department_router = APIRouter(prefix="/api/departments", tags=["departments"])
position_router = APIRouter(prefix="/api/positions", tags=["positions"])
document_router = APIRouter(prefix="/api/documents", tags=["documents"])
contract_router = APIRouter(prefix="/api/contracts", tags=["contracts"])
contract_template_router = APIRouter(prefix="/api/contract-templates", tags=["contract-templates"])
amendment_router = APIRouter(prefix="/api/contract-amendments", tags=["contract-amendments"])

# ---------------------------------------------------------------------------
# Employee endpoints
# ---------------------------------------------------------------------------


@employee_router.get("", response_model=EmployeeListResponse)
async def list_employees(
    current_user: CurrentUserDep,
    current_employee: CurrentUserEmployee,
    employee_service: EmployeeServiceDep,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search in name or email"),
    department_id: UUID | None = Query(default=None, description="Filter by department"),
    position_id: UUID | None = Query(default=None, description="Filter by position"),
    is_active: bool | None = Query(default=True, description="Filter by active status"),
) -> EmployeeListResponse:
    """List employees with pagination and optional filters.

    Ownership check: non-admin employees can only see their own profile.
    """
    if current_user.role != "admin":
        if current_employee is None:
            return EmployeeListResponse(items=[], total=0, page=1, page_size=page_size)
        return EmployeeListResponse(
            items=[EmployeeResponse.model_validate(current_employee)],
            total=1,
            page=1,
            page_size=page_size,
        )

    items, total = await employee_service.list_employees(
        page=page,
        page_size=page_size,
        search=search,
        department_id=department_id,
        position_id=position_id,
        is_active=is_active,
    )
    return EmployeeListResponse(
        items=[EmployeeResponse.model_validate(emp) for emp in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@employee_router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    current_user: CurrentUserDep,
    current_employee: CurrentUserEmployee,
    employee_service: EmployeeServiceDep,
) -> EmployeeResponse:
    """Get a single employee by ID.

    Ownership check: non-admin employees can only view their own profile.
    """
    employee = await employee_service.get_employee(employee_id)
    if current_user.role != "admin":
        if current_employee is None or employee.id != current_employee.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot view another employee's profile",
            )
    return EmployeeResponse.model_validate(employee)


@employee_router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    body: EmployeeCreate,
    current_user: AdminUserDep,
    employee_service: EmployeeServiceDep,
) -> EmployeeResponse:
    """Create a new employee."""
    data = body.model_dump(exclude_unset=True)
    employee = await employee_service.create_employee(data)
    return EmployeeResponse.model_validate(employee)


@employee_router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    body: EmployeeUpdate,
    current_user: CurrentUserDep,
    current_employee: CurrentUserEmployee,
    employee_service: EmployeeServiceDep,
) -> EmployeeResponse:
    """Update an existing employee.

    Self-edit restriction: employees can only update phone and address.
    """
    data = body.model_dump(exclude_unset=True)
    if current_user.role != "admin":
        allowed_fields = {"phone", "address"}
        disallowed = set(data.keys()) - allowed_fields
        if disallowed:
            raise HTTPException(
                status_code=403,
                detail="Employees can only update phone and address. Disallowed: "
                f"{', '.join(sorted(disallowed))}",
            )
        if current_employee is None or employee_id != current_employee.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot update another employee",
            )
    employee = await employee_service.update_employee(
        employee_id,
        data,
        actor_hr_id=current_user.id,
    )
    return EmployeeResponse.model_validate(employee)


@employee_router.delete("/{employee_id}", response_model=EmployeeResponse)
async def delete_employee(
    employee_id: UUID,
    current_user: AdminUserDep,
    employee_service: EmployeeServiceDep,
) -> EmployeeResponse:
    """Soft-delete an employee (set is_active=False)."""
    employee = await employee_service.delete_employee(employee_id)
    return EmployeeResponse.model_validate(employee)


@employee_router.post("/promote", response_model=EmployeeResponse, status_code=201)
async def promote_candidate(
    body: PromoteCandidateRequest,
    current_user: AdminUserDep,
    employee_service: EmployeeServiceDep,
) -> EmployeeResponse:
    """Promote a candidate to employee."""
    data = body.model_dump(exclude_unset=True)
    employee = await employee_service.promote_candidate(data)
    return EmployeeResponse.model_validate(employee)


@employee_router.post("/import", response_model=ImportResult)
async def import_employees(
    current_user: AdminUserDep,
    import_service: ImportServiceDep,
    file: UploadFile = File(..., description="Excel .xlsx file to import"),
) -> ImportResult:
    """Import employees from an Excel (.xlsx) file."""
    file_bytes = await file.read()
    result = await import_service.import_from_excel(file_bytes)
    return ImportResult(**result)


# ---------------------------------------------------------------------------
# Employee document endpoints
# ---------------------------------------------------------------------------


@employee_router.get("/{employee_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    employee_id: UUID,
    current_user: CurrentUserDep,
    current_employee: CurrentUserEmployee,
    document_service: DocumentServiceDep,
) -> list[DocumentResponse]:
    """List all documents for an employee.

    Ownership check: employees can only view their own documents.
    """
    if current_user.role != "admin":
        if current_employee is None or employee_id != current_employee.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot view another employee's documents",
            )
    documents = await document_service.list_documents(employee_id)
    return [DocumentResponse.model_validate(doc) for doc in documents]


@employee_router.post(
    "/{employee_id}/documents",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    employee_id: UUID,
    current_user: CurrentUserDep,
    current_employee: CurrentUserEmployee,
    document_service: DocumentServiceDep,
    file: UploadFile = File(..., description="Document file to upload"),
    document_type: str = Form(..., description="Document category"),
    description: str | None = Form(default=None, description="Optional document description"),
) -> DocumentResponse:
    """Upload a document to an employee's document vault.

    Ownership check: employees can only upload to their own vault.
    """
    if current_user.role != "admin":
        if current_employee is None or employee_id != current_employee.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot upload to another employee's documents",
            )

    file_data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    file_name = file.filename or "unnamed"

    document = await document_service.upload_document(
        employee_id=employee_id,
        document_type=document_type,
        file_name=file_name,
        file_data=file_data,
        content_type=content_type,
    )
    return DocumentResponse.model_validate(document)


# ---------------------------------------------------------------------------
# Document download/delete endpoints (by document ID)
# ---------------------------------------------------------------------------


@document_router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    current_employee: CurrentUserEmployee,
    document_service: DocumentServiceDep,
) -> Response:
    """Download a document by its ID.

    Ownership check: employees can only download their own documents.
    Fetches metadata first, checks ownership, then downloads from MinIO.
    """
    document = await document_service.get_document_metadata(document_id)

    if current_user.role != "admin":
        if current_employee is None or document.employee_id != current_employee.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot download another employee's document",
            )

    file_data = await document_service.download_file(document.storage_path)

    return Response(
        content=file_data,
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.file_name}"',
        },
    )


@document_router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    current_user: AdminUserDep,
    document_service: DocumentServiceDep,
) -> None:
    """Delete a document by its ID.

    Only admins can delete documents.
    """
    await document_service.delete_document(document_id)


# ---------------------------------------------------------------------------
# Department endpoints
# ---------------------------------------------------------------------------


@department_router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    current_user: CurrentUserDep,
    department_service: DepartmentServiceDep,
) -> list[DepartmentResponse]:
    """List all departments."""
    departments = await department_service.list_departments()
    return [DepartmentResponse.model_validate(dept) for dept in departments]


@department_router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    body: DepartmentCreate,
    current_user: AdminUserDep,
    department_service: DepartmentServiceDep,
) -> DepartmentResponse:
    """Create a new department."""
    data = body.model_dump(exclude_unset=True)
    department = await department_service.create_department(data)
    return DepartmentResponse.model_validate(department)


@department_router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    body: DepartmentUpdate,
    current_user: AdminUserDep,
    department_service: DepartmentServiceDep,
) -> DepartmentResponse:
    """Update an existing department."""
    data = body.model_dump(exclude_unset=True)
    department = await department_service.update_department(department_id, data)
    return DepartmentResponse.model_validate(department)


@department_router.delete("/{department_id}", status_code=204)
async def delete_department(
    department_id: UUID,
    current_user: AdminUserDep,
    department_service: DepartmentServiceDep,
) -> None:
    """Delete a department (cascade-protected)."""
    await department_service.delete_department(department_id)


# ---------------------------------------------------------------------------
# Position endpoints
# ---------------------------------------------------------------------------


@position_router.get("", response_model=list[PositionResponse])
async def list_positions(
    current_user: CurrentUserDep,
    position_service: PositionServiceDep,
) -> list[PositionResponse]:
    """List all positions."""
    positions = await position_service.list_positions()
    return [PositionResponse.model_validate(pos) for pos in positions]


@position_router.post("", response_model=PositionResponse, status_code=201)
async def create_position(
    body: PositionCreate,
    current_user: AdminUserDep,
    position_service: PositionServiceDep,
) -> PositionResponse:
    """Create a new position."""
    data = body.model_dump(exclude_unset=True)
    position = await position_service.create_position(data)
    return PositionResponse.model_validate(position)


@position_router.put("/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: UUID,
    body: PositionUpdate,
    current_user: AdminUserDep,
    position_service: PositionServiceDep,
) -> PositionResponse:
    """Update an existing position."""
    data = body.model_dump(exclude_unset=True)
    position = await position_service.update_position(position_id, data)
    return PositionResponse.model_validate(position)


@position_router.delete("/{position_id}", status_code=204)
async def delete_position(
    position_id: UUID,
    current_user: AdminUserDep,
    position_service: PositionServiceDep,
) -> None:
    """Delete a position (cascade-protected)."""
    await position_service.delete_position(position_id)


# ---------------------------------------------------------------------------
# Contract endpoints
# ---------------------------------------------------------------------------

@employee_router.get("/{employee_id}/contracts", response_model=list[ContractResponse])
async def list_employee_contracts(
    employee_id: UUID,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> list[ContractResponse]:
    contracts = await contract_service.list_by_employee(employee_id)
    return [ContractResponse.model_validate(contract) for contract in contracts]

@employee_router.post("/{employee_id}/contracts", response_model=ContractResponse, status_code=201)
async def create_employee_contract(
    employee_id: UUID,
    body: ContractCreate,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    data = body.model_dump(exclude_unset=True)
    data["employee_id"] = employee_id
    contract = await contract_service.create_contract(data, created_by=current_user.id, actor_id=current_user.id)
    return ContractResponse.model_validate(contract)

@contract_router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: UUID,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    contract = await contract_service.get_by_id(contract_id)
    return ContractResponse.model_validate(contract)

@contract_router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    body: ContractUpdate,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    contract = await contract_service.update_draft(contract_id, body.model_dump(exclude_unset=True))
    return ContractResponse.model_validate(contract)

@contract_router.post("/{contract_id}/send-for-signing", response_model=ContractResponse)
async def send_contract_for_signing(
    contract_id: UUID,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    contract = await contract_service.mark_sending(contract_id, current_user.id)
    return ContractResponse.model_validate(contract)

@contract_router.post("/{contract_id}/sign", response_model=ContractResponse)
async def sign_contract(
    contract_id: UUID,
    body: ContractSignRequest,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    contract = await contract_service.sign(
        contract_id,
        current_user.id,
        signed_doc_path=body.signed_document_path,
        signed_on=body.signed_on,
    )
    return ContractResponse.model_validate(contract)

@contract_router.post("/{contract_id}/renew", response_model=ContractResponse)
async def renew_contract(
    contract_id: UUID,
    body: ContractRenewRequest,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    contract = await contract_service.renew(
        contract_id,
        current_user.id,
        new_started_on=body.new_started_on,
        new_ended_on=body.new_ended_on,
        new_content=body.new_content,
    )
    return ContractResponse.model_validate(contract)

@contract_router.post("/{contract_id}/terminate", response_model=ContractResponse)
async def terminate_contract(
    contract_id: UUID,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    contract = await contract_service.terminate(contract_id, current_user.id)
    return ContractResponse.model_validate(contract)

@contract_router.post("/{contract_id}/cancel", response_model=ContractResponse)
async def cancel_contract(
    contract_id: UUID,
    current_user: AdminUserDep,
    contract_service: ContractServiceDep,
) -> ContractResponse:
    contract = await contract_service.cancel(contract_id, current_user.id)
    return ContractResponse.model_validate(contract)

@contract_template_router.get("", response_model=list[ContractTemplateResponse])
async def list_contract_templates(
    current_user: AdminUserDep,
    template_service: ContractTemplateServiceDep,
) -> list[ContractTemplateResponse]:
    templates = await template_service.list_active()
    return [ContractTemplateResponse.model_validate(template) for template in templates]

@contract_template_router.post("", response_model=ContractTemplateResponse, status_code=201)
async def create_contract_template(
    body: ContractTemplateCreate,
    current_user: AdminUserDep,
    template_service: ContractTemplateServiceDep,
) -> ContractTemplateResponse:
    template = await template_service.create(body.model_dump(exclude_unset=True), created_by=current_user.id)
    return ContractTemplateResponse.model_validate(template)

@contract_template_router.put("/{template_id}", response_model=ContractTemplateResponse)
async def update_contract_template(
    template_id: UUID,
    body: ContractTemplateUpdate,
    current_user: AdminUserDep,
    template_service: ContractTemplateServiceDep,
) -> ContractTemplateResponse:
    template = await template_service.update(template_id, body.model_dump(exclude_unset=True))
    return ContractTemplateResponse.model_validate(template)

@contract_template_router.post("/{template_id}/archive", response_model=ContractTemplateResponse)
async def archive_contract_template(
    template_id: UUID,
    current_user: AdminUserDep,
    template_service: ContractTemplateServiceDep,
) -> ContractTemplateResponse:
    template = await template_service.archive(template_id)
    return ContractTemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Contract Amendment endpoints
# ---------------------------------------------------------------------------

@contract_router.get("/{contract_id}/amendments", response_model=list[ContractAmendmentResponse])
async def list_contract_amendments(
    contract_id: UUID,
    current_user: AdminUserDep,
    amendment_service: ContractAmendmentServiceDep,
) -> list[ContractAmendmentResponse]:
    amendments = await amendment_service.list_by_contract(contract_id)
    return [ContractAmendmentResponse.model_validate(a) for a in amendments]

@contract_router.post("/{contract_id}/amendments", response_model=ContractAmendmentResponse, status_code=201)
async def create_contract_amendment(
    contract_id: UUID,
    body: ContractAmendmentCreate,
    current_user: AdminUserDep,
    amendment_service: ContractAmendmentServiceDep,
) -> ContractAmendmentResponse:
    data = body.model_dump(exclude_unset=True)
    data["contract_id"] = contract_id
    amendment = await amendment_service.create(data, created_by=current_user.id)
    return ContractAmendmentResponse.model_validate(amendment)

@amendment_router.put("/{amendment_id}", response_model=ContractAmendmentResponse)
async def update_amendment(
    amendment_id: UUID,
    body: ContractAmendmentCreate,
    current_user: AdminUserDep,
    amendment_service: ContractAmendmentServiceDep,
) -> ContractAmendmentResponse:
    amendment = await amendment_service.update(amendment_id, body.model_dump(exclude_unset=True))
    return ContractAmendmentResponse.model_validate(amendment)

# ---------------------------------------------------------------------------
# Employment event endpoints
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------


@employee_router.get("/{employee_id}/events", response_model=list[EmploymentEventResponse])
async def list_employment_events(
    employee_id: UUID,
    current_user: CurrentUserDep,
    current_employee: CurrentUserEmployee,
    event_service: EmploymentEventServiceDep,
) -> list[EmploymentEventResponse]:
    if current_user.role != "admin":
        if current_employee is None or employee_id != current_employee.id:
            raise HTTPException(status_code=403, detail="Access denied")
    events = await event_service.list_by_employee(employee_id)
    return [EmploymentEventResponse.model_validate(evt) for evt in events]


@employee_router.patch("/{employee_id}/status", response_model=EmployeeResponse)
async def change_employee_status(
    employee_id: UUID,
    body: EmployeeStatusChangeRequest,
    current_user: AdminUserDep,
    employee_service: EmployeeServiceDep,
) -> EmployeeResponse:
    employee = await employee_service.change_status(
        employee_id,
        body.status,
        actor_hr_id=current_user.id,
        termination_date=body.termination_date,
        note=body.note,
    )
    return EmployeeResponse.model_validate(employee)


# ---------------------------------------------------------------------------
# Document status endpoints
# ---------------------------------------------------------------------------


@document_router.post("/{document_id}/verify", response_model=DocumentResponse)
async def verify_document(
    document_id: UUID,
    current_user: AdminUserDep,
    document_service: DocumentServiceDep,
) -> DocumentResponse:
    document = await document_service.verify_document(document_id, current_user.id)
    return DocumentResponse.model_validate(document)


@document_router.post("/{document_id}/reject", response_model=DocumentResponse)
async def reject_document(
    document_id: UUID,
    body: DocumentRejectRequest,
    current_user: AdminUserDep,
    document_service: DocumentServiceDep,
) -> DocumentResponse:
    document = await document_service.reject_document(document_id, current_user.id, body.note)
    return DocumentResponse.model_validate(document)


@document_router.post("/{document_id}/expire", response_model=DocumentResponse)
async def expire_document(
    document_id: UUID,
    current_user: AdminUserDep,
    document_service: DocumentServiceDep,
) -> DocumentResponse:
    document = await document_service.mark_expired(document_id)
    return DocumentResponse.model_validate(document)

# ---------------------------------------------------------------------------
# Include sub-routers into the main router
# ---------------------------------------------------------------------------

router.include_router(employee_router)
router.include_router(department_router)
router.include_router(position_router)
router.include_router(document_router)
router.include_router(contract_router)
router.include_router(contract_template_router)
router.include_router(amendment_router)
