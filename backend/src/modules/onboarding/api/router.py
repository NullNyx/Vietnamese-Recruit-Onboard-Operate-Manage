"""FastAPI router for the Onboarding module.

Defines the ``/api/onboarding`` endpoints (tag ``onboarding``) HR uses to view
onboarding processes and drive them to completion:

* ``GET /api/onboarding/processes`` — list processes with progress, paginated
  (``<= 50``) with an optional ``status`` filter (admin only, R6.1, R6.2, R6.4,
  R6.5).
* ``GET /api/onboarding/processes/{process_id}`` — one process with its full
  checklist (admin only, R6.3, R6.6).
* ``PATCH /api/onboarding/tasks/{task_id}`` — set a task's status (used to mark
  it ``done``), which activates the linked employee once every task is done
  (R4.1, R4.4, R4.5, R4.6, R5.5).

Authorization ordering
----------------------
The two ``GET`` endpoints enforce the ``admin`` role with the ``require_admin``
route dependency (mirrored from ``identity.api.admin_router.require_admin``).

``PATCH /tasks/{task_id}`` must, per R4.4, evaluate task *existence* (404)
before requester *authorization* (403), so it deliberately does **not** use
``require_admin`` as a dependency. Instead it resolves the authenticated user
via ``get_current_user`` and passes them to
:meth:`OnboardingService.complete_task`, which performs the checks in the
mandated order: path validation (UUID + status enum) → 422 (handled by FastAPI
/ Pydantic before the handler runs), task existence → 404, actor role
``admin`` → 403, then the state change.

Path params are typed as :class:`~uuid.UUID` so a malformed identifier yields a
422 automatically (R4.6); the ``status`` filter query param is typed as
:class:`~src.modules.onboarding.domain.enums.OnboardingStatus` so an undefined
value is rejected with a 422 before any query runs (R6.5); the PATCH body is
:class:`~src.modules.onboarding.api.schemas.TaskStatusUpdate` whose ``status``
field is constrained to ``{pending, done}`` (R3.5, R4.6).

Domain errors raised by the service (``OnboardingProcessNotFoundError`` 404,
``OnboardingTaskNotFoundError`` 404, ``OnboardingAuthorizationError`` 403,
``InvalidTaskStatusError`` 422, ...) are translated to JSON by
``register_onboarding_error_handlers`` (registered with the app), so the router
lets them propagate rather than catching them.

Requirements: 4.1, 4.4, 4.5, 4.6, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.employee.infrastructure.employee_repository import EmployeeRepository
from src.modules.identity.api.admin_router import require_admin
from src.modules.identity.container import get_current_user, get_db_session
from src.modules.identity.domain.entities import User
from src.modules.onboarding.api.schemas import (
    ContractDraftResponse,
    ContractDraftStatusUpdate,
    ContractDraftUpdate,
    DocumentUploadResponse,
    DocumentVerifyRequest,
    EmployeeSetupUpdate,
    OnboardingCountsResponse,
    OnboardingDocumentResponse,
    OnboardingProcessDetailResponse,
    OnboardingProcessListItem,
    OnboardingProcessListResponse,
    OnboardingTaskResponse,
    TaskStatusUpdate,
)
from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.container import get_onboarding_service
from src.modules.onboarding.domain.enums import OnboardingStatus, OnboardingTaskStatus
from src.modules.onboarding.domain.exceptions import OnboardingContractNotFoundError
from src.modules.onboarding.infrastructure.document_repository import OnboardingDocumentRepository
from src.modules.recruitment.domain.entities import Candidate
from src.modules.recruitment.infrastructure.repositories import (
    CandidateRepository,
    JobOpeningRepository,
)

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------

OnboardingServiceDep = Annotated[OnboardingService, Depends(get_onboarding_service)]
AdminUserDep = Annotated[User, Depends(require_admin)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

onboarding_router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# ---------------------------------------------------------------------------
# List onboarding processes
# ---------------------------------------------------------------------------


@onboarding_router.get("/counts", response_model=OnboardingCountsResponse)
async def get_counts(
    _admin: AdminUserDep,
    onboarding_service: OnboardingServiceDep,
) -> OnboardingCountsResponse:
    """Return aggregate process counts by status for tab badges.

    Read-only endpoint returning the true totals for each status so the
    frontend can render accurate badge counts on filter tabs without
    loading any process items.

    Args:
        _admin: The authenticated admin user (admin-only).
        onboarding_service: The onboarding application service.

    Returns:
        Counts for total, in_progress, and complete.
    """
    counts = await onboarding_service.get_counts()
    return OnboardingCountsResponse(**counts)


@onboarding_router.get("/processes", response_model=OnboardingProcessListResponse)
async def list_processes(
    _admin: AdminUserDep,
    onboarding_service: OnboardingServiceDep,
    status: OnboardingStatus | None = Query(
        default=None, description="Filter by status: in_progress, ready_for_completion, complete"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=50, ge=1, le=50, description="Items per page (capped at 50)"),
) -> OnboardingProcessListResponse:
    """List onboarding processes with progress, paginated and capped at 50.

    Returns at most 50 processes for the requested page together with the true
    total of processes matching the request (zero with an empty list when none
    match). When ``status`` is supplied only processes whose status is identical
    to it are returned; an undefined ``status`` value is rejected by
    FastAPI/Pydantic with a 422 before this handler runs (R6.5). Admin only
    (R6.1, R6.2, R6.4).

    Args:
        _admin: The authenticated admin user (enforces admin-only access).
        onboarding_service: The onboarding application service.
        status: Optional process-status filter (``in_progress`` or
            ``complete``); ``None`` returns processes of every status.
        page: The 1-indexed page number.
        page_size: Items per page (1-50; the service caps this at 50).

    Returns:
        The paginated list of process items with the true matching total.
    """
    result = await onboarding_service.list_processes(
        status=status.value if status is not None else None,
        page=page,
        page_size=page_size,
    )

    items = []
    for item in result.items:
        items.append(
            OnboardingProcessListItem(
                id=item.process_id,
                status=OnboardingStatus(item.status),
                employee_id=item.employee_id,
                employee_full_name=item.employee_full_name,
                employee_email=item.employee_email,
                employee_code=item.employee_code,
                completed_count=item.completed_count,
                total_count=item.total_count,
                missing_setup_fields=item.missing_setup_fields,
            )
        )

    return OnboardingProcessListResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# ---------------------------------------------------------------------------
# Get onboarding process detail
# ---------------------------------------------------------------------------


@onboarding_router.get(
    "/processes/{process_id}",
    response_model=OnboardingProcessDetailResponse,
)
async def get_process(
    process_id: UUID,
    _admin: AdminUserDep,
    onboarding_service: OnboardingServiceDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingProcessDetailResponse:
    """Get one onboarding process with its full checklist.

    Returns the process summary plus each task's name and current status,
    ordered by ``order_index`` (R6.3). A malformed ``process_id`` yields a 422
    automatically (R4.6); an unknown ``process_id`` raises
    ``OnboardingProcessNotFoundError`` → 404 with no process data (R6.6). Admin
    only.

    Args:
        process_id: The identifier of the onboarding process to load.
        _admin: The authenticated admin user (enforces admin-only access).
        onboarding_service: The onboarding application service.

    Returns:
        The full process detail including its checklist.

    Raises:
        OnboardingProcessNotFoundError: If no process exists for ``process_id``.
    """
    detail = await onboarding_service.get_process(process_id)

    # Enrich with employee data
    emp_repo = EmployeeRepository(db_session)
    employee = await emp_repo.get_by_id(detail.employee_id)

    # Enrich with candidate data
    candidate_repo = CandidateRepository(db_session)
    candidate = await candidate_repo.get_by_id(detail.candidate_id)
    document_repo = OnboardingDocumentRepository(db_session)
    documents = await document_repo.list_by_process(process_id)
    return OnboardingProcessDetailResponse(
        id=detail.process_id,
        status=OnboardingStatus(detail.status),
        employee_id=detail.employee_id,
        employee_full_name=employee.full_name if employee else "",
        employee_email=employee.email if employee else "",
        employee_code=employee.employee_code if employee else None,
        completed_count=detail.completed_count,
        total_count=detail.total_count,
        missing_setup_fields=detail.missing_setup_fields,
        completed_at=detail.completed_at,
        department_id=detail.department_id,
        position_id=detail.position_id,
        manager_id=detail.manager_id,
        start_date=detail.start_date.isoformat() if detail.start_date else None,
        accepted_at=(
            candidate.accepted_at.isoformat() if candidate and candidate.accepted_at else None
        ),
        job_opening=await _resolve_job_opening(candidate, db_session),
        documents=[OnboardingDocumentResponse.model_validate(doc) for doc in documents],
        contract_draft=await _resolve_contract_draft(process_id, db_session),
        tasks=[
            OnboardingTaskResponse(
                id=task.id,
                name=task.name,
                status=OnboardingTaskStatus(task.status),
                order_index=task.order_index,
                completed_at=task.completed_at,
                completed_by_name=task.completed_by_name,
            )
            for task in detail.tasks
        ],
    )


async def _resolve_job_opening(
    candidate: Candidate | None,
    db_session: AsyncSession,
) -> str | None:
    """Resolve Job Opening title from candidate, if assigned."""
    if not candidate or not candidate.job_opening_id:
        return None
    jo_repo = JobOpeningRepository(db_session)
    jo = await jo_repo.get_by_id(candidate.job_opening_id)
    return jo.title if jo else None


# ---------------------------------------------------------------------------
# Update an onboarding task status (mark done)
# ---------------------------------------------------------------------------


@onboarding_router.patch("/tasks/{task_id}", response_model=OnboardingTaskResponse)
async def update_task(
    task_id: UUID,
    body: TaskStatusUpdate,
    current_user: CurrentUserDep,
    onboarding_service: OnboardingServiceDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingTaskResponse:
    """Set an onboarding task's status (used to mark it ``done``).

    Marking the last remaining ``pending`` task ``done`` completes the process
    and activates the linked employee within the same transaction (R5.5). The
    ``task_id`` path param (UUID) and the ``status`` body field
    (``{pending, done}``) are validated by FastAPI/Pydantic, so a malformed UUID
    or an invalid status yields a 422 before this handler runs (R3.5, R4.6).

    Authorization deliberately follows existence: this endpoint resolves the
    user via ``get_current_user`` (not ``require_admin``) and delegates to
    :meth:`OnboardingService.complete_task`, which checks task existence (404)
    before the actor's ``admin`` role (403) per R4.4/R4.5.

    Args:
        task_id: The identifier of the task to update.
        body: The requested task status (``pending`` or ``done``).
        current_user: The authenticated user performing the action.
        onboarding_service: The onboarding application service.

    Returns:
        The task in its resulting state.

    Raises:
        OnboardingTaskNotFoundError: If no task exists for ``task_id`` (404).
        OnboardingAuthorizationError: If the actor is not an admin (403).
        InvalidTaskStatusError: If the status value is not ``pending``/``done``.
        AuditWriteError: If a mandatory audit append fails (state unchanged).
        OnboardingActivationError: If completion/activation fails (unchanged).
    """
    task = await onboarding_service.complete_task(
        task_id=task_id,
        actor=current_user,
        status=body.status.value,
    )

    completed_by_name = None
    if task.status == OnboardingTaskStatus.DONE.value:
        if task.completed_by_user_id == current_user.id:
            completed_by_name = current_user.name
        elif task.completed_by_user_id is not None:
            user = await db_session.get(User, task.completed_by_user_id)
            completed_by_name = user.name if user else None

    return OnboardingTaskResponse(
        id=task.id,
        name=task.name,
        status=OnboardingTaskStatus(task.status),
        order_index=task.order_index,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        completed_by_name=completed_by_name,
    )


# ---------------------------------------------------------------------------
# Confirm onboarding completion
# ---------------------------------------------------------------------------


@onboarding_router.patch(
    "/processes/{process_id}/complete",
    response_model=OnboardingProcessDetailResponse,
)
async def confirm_completion(
    process_id: UUID,
    current_user: CurrentUserDep,
    onboarding_service: OnboardingServiceDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingProcessDetailResponse:
    """Confirm completion of a ready onboarding process.

    The process must be in ``ready_for_completion`` status. On confirmation
    the process transitions to ``complete`` and the linked employee is
    activated (``is_active = true``). Admin only.

    Args:
        process_id: The identifier of the process to complete.
        current_user: The authenticated admin user.
        onboarding_service: The onboarding application service.

    Returns:
        The updated process detail with ``complete`` status.
    """
    await onboarding_service.confirm_completion(
        process_id=process_id,
        actor=current_user,
    )

    detail = await onboarding_service.get_process(process_id)
    emp_repo = EmployeeRepository(db_session)
    employee = await emp_repo.get_by_id(detail.employee_id)
    candidate_repo = CandidateRepository(db_session)
    candidate = await candidate_repo.get_by_id(detail.candidate_id)
    document_repo = OnboardingDocumentRepository(db_session)
    documents = await document_repo.list_by_process(process_id)
    return OnboardingProcessDetailResponse(
        id=detail.process_id,
        status=OnboardingStatus(detail.status),
        employee_id=detail.employee_id,
        employee_full_name=employee.full_name if employee else "",
        employee_email=employee.email if employee else "",
        employee_code=employee.employee_code if employee else None,
        completed_count=detail.completed_count,
        total_count=detail.total_count,
        missing_setup_fields=detail.missing_setup_fields,
        completed_at=detail.completed_at,
        department_id=detail.department_id,
        position_id=detail.position_id,
        manager_id=detail.manager_id,
        start_date=detail.start_date.isoformat() if detail.start_date else None,
        accepted_at=(
            candidate.accepted_at.isoformat() if candidate and candidate.accepted_at else None
        ),
        job_opening=await _resolve_job_opening(candidate, db_session),
        documents=[OnboardingDocumentResponse.model_validate(doc) for doc in documents],
        contract_draft=await _resolve_contract_draft(process_id, db_session),
        tasks=[
            OnboardingTaskResponse(
                id=task.id,
                name=task.name,
                status=OnboardingTaskStatus(task.status),
                order_index=task.order_index,
                completed_at=task.completed_at,
                completed_by_name=task.completed_by_name,
            )
            for task in detail.tasks
        ],
    )


# ---------------------------------------------------------------------------
# Update employee setup fields
# ---------------------------------------------------------------------------


@onboarding_router.patch(
    "/processes/{process_id}/employee-setup",
    response_model=OnboardingProcessDetailResponse,
)
async def update_employee_setup(
    process_id: UUID,
    body: EmployeeSetupUpdate,
    current_user: CurrentUserDep,
    onboarding_service: OnboardingServiceDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingProcessDetailResponse:
    """Update an inactive Employee's core setup fields from the onboarding workspace.

    Args:
        process_id: The identifier of the onboarding process.
        body: The employee setup fields to update.
        current_user: The authenticated user performing the action.
        onboarding_service: The onboarding application service.
        db_session: Database session for enriching the response.

    Returns:
        The updated process detail.
    """
    await onboarding_service.update_employee_setup(
        process_id=process_id,
        actor=current_user,
        data=body.model_dump(exclude_unset=True),
    )

    # Delegate back to get_process for enriched response
    return await get_process(process_id, current_user, onboarding_service, db_session)


# ---------------------------------------------------------------------------
# Document management endpoints
# ---------------------------------------------------------------------------


@onboarding_router.get(
    "/processes/{process_id}/documents",
    response_model=list[OnboardingDocumentResponse],
)
async def list_documents(
    process_id: UUID,
    _admin: AdminUserDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[OnboardingDocumentResponse]:
    """List document items for an onboarding process, initialising from template if none exist."""
    from src.modules.onboarding.domain.entities import OnboardingDocument
    from src.modules.onboarding.domain.enums import DOCUMENT_TEMPLATE

    repo = OnboardingDocumentRepository(db_session)
    docs = await repo.list_by_process(process_id)
    if not docs:
        docs = [
            OnboardingDocument(
                process_id=process_id,
                document_type=doc_type,
                display_name=display_name,
                is_required=is_required,
                status="pending",
            )
            for doc_type, display_name, is_required in DOCUMENT_TEMPLATE
        ]
        docs = await repo.create_many(docs)
    return [OnboardingDocumentResponse.model_validate(d) for d in docs]


@onboarding_router.patch("/documents/{document_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    file: UploadFile = File(None),
) -> DocumentUploadResponse:
    """Record a file upload for a document item.

    When a file is provided it is stored in MinIO via the employee module's
    MinIO client. Without a file the endpoint just updates the document status
    (for AI-simulated or placeholder uploads).
    """
    from fastapi import HTTPException

    repo = OnboardingDocumentRepository(db_session)
    doc = await repo.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if file:
        content = await file.read()
        bucket_path = f"onboarding/{doc.process_id}/{document_id}/{file.filename or 'upload'}"
        try:
            from src.modules.employee.container import get_minio_client
            from src.modules.employee.infrastructure.minio_client import MinIOClient

            minio: MinIOClient = get_minio_client()
            await minio.upload_file(
                bucket_path,
                content,
                file.content_type or "application/octet-stream",
            )
        except Exception:
            raise HTTPException(status_code=500, detail="File upload to storage failed")

        doc.status = "uploaded"
        doc.file_name = file.filename
        doc.file_size = len(content)
        doc.mime_type = file.content_type or "application/octet-stream"
        doc.storage_path = bucket_path
    else:
        doc.status = "uploaded"

    doc.uploaded_by_hr_id = current_user.id
    doc.uploaded_at = datetime.now(UTC)
    await repo.update(doc)
    return DocumentUploadResponse(
        id=doc.id,
        status=doc.status,
        file_name=doc.file_name or "",
        file_size=doc.file_size or 0,
        mime_type=doc.mime_type or "",
    )


@onboarding_router.patch(
    "/documents/{document_id}/verify",
    response_model=OnboardingDocumentResponse,
)
async def verify_document(
    document_id: UUID,
    body: DocumentVerifyRequest,
    current_user: CurrentUserDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingDocumentResponse:
    """Verify or reject a document item."""
    repo = OnboardingDocumentRepository(db_session)
    doc = await repo.get_by_id(document_id)
    if doc is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Document not found")
    if body.verified:
        doc.status = "verified"
        doc.verified_at = datetime.now(UTC)
        doc.verified_by_hr_id = current_user.id
        doc.reject_reason = None
    else:
        doc.status = "rejected"
        doc.verified_at = datetime.now(UTC)
        doc.verified_by_hr_id = current_user.id
        doc.reject_reason = body.reject_reason
    await repo.update(doc)
    return OnboardingDocumentResponse.model_validate(doc)

# ---------------------------------------------------------------------------
# Contract helpers and endpoints
# ---------------------------------------------------------------------------


async def _resolve_contract_draft(
    process_id: UUID,
    db_session: AsyncSession,
) -> ContractDraftResponse | None:
    """Load the contract draft for an onboarding process, if one exists."""
    try:
        from src.modules.onboarding.domain.entities import OnboardingContractDraft
        from src.modules.onboarding.infrastructure.contract_repository import OnboardingContractRepository

        repo = OnboardingContractRepository(db_session)
        draft = await repo.get_by_process(process_id)
        if draft is None:
            return None
        return ContractDraftResponse(
            id=draft.id,
            process_id=draft.process_id,
            contract_type=draft.contract_type,
            content=draft.content,
            status=draft.status,
            revision=getattr(draft, "revision", 1),
            created_by=draft.created_by,
            updated_by=draft.updated_by,
            created_at=draft.created_at.isoformat() if draft.created_at else "",
            updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
        )
    except Exception:
        return None


@onboarding_router.get(
    "/processes/{process_id}/contract",
    response_model=ContractDraftResponse,
)
async def get_contract_draft(
    process_id: UUID,
    _admin: AdminUserDep,
    onboarding_service: OnboardingServiceDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ContractDraftResponse:
    """Return the contract draft for an onboarding process, or 404."""
    draft = await onboarding_service.get_contract_draft(process_id)
    return ContractDraftResponse(
        id=draft.id,
        process_id=draft.process_id,
        contract_type=draft.contract_type,
        content=draft.content,
        status=draft.status,
        revision=draft.revision,
        created_by=draft.created_by,
        updated_by=draft.updated_by,
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
    )


@onboarding_router.patch(
    "/processes/{process_id}/contract",
    response_model=ContractDraftResponse,
)
async def update_contract_draft(
    process_id: UUID,
    body: ContractDraftUpdate,
    current_user: CurrentUserDep,
    onboarding_service: OnboardingServiceDep,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ContractDraftResponse:
    """Edit the contract draft content and/or type."""
    draft = await onboarding_service.update_contract_draft(
        process_id=process_id,
        actor=current_user,
        data=body.model_dump(exclude_unset=True),
    )
    return ContractDraftResponse(
        id=draft.id,
        process_id=draft.process_id,
        contract_type=draft.contract_type,
        content=draft.content,
        status=draft.status,
        revision=draft.revision,
        created_by=draft.created_by,
        updated_by=draft.updated_by,
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
    )


@onboarding_router.patch(
    "/processes/{process_id}/contract/generate",
    response_model=ContractDraftResponse,
)
async def generate_contract_draft(
    process_id: UUID,
    current_user: CurrentUserDep,
    onboarding_service: OnboardingServiceDep,
) -> ContractDraftResponse:
    """Trigger AI draft content generation (placeholder)."""
    draft = await onboarding_service.generate_contract_draft(
        process_id=process_id,
        actor=current_user,
    )
    return ContractDraftResponse(
        id=draft.id,
        process_id=draft.process_id,
        contract_type=draft.contract_type,
        content=draft.content,
        status=draft.status,
        revision=draft.revision,
        created_by=draft.created_by,
        updated_by=draft.updated_by,
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
    )


@onboarding_router.patch(
    "/processes/{process_id}/contract/status",
    response_model=ContractDraftResponse,
)
async def update_contract_status(
    process_id: UUID,
    body: ContractDraftStatusUpdate,
    current_user: CurrentUserDep,
    onboarding_service: OnboardingServiceDep,
) -> ContractDraftResponse:
    """Advance contract draft status (draft -> ready -> sent -> signed)."""
    draft = await onboarding_service.update_contract_status(
        process_id=process_id,
        actor=current_user,
        status=body.status,
    )
    return ContractDraftResponse(
        id=draft.id,
        process_id=draft.process_id,
        contract_type=draft.contract_type,
        content=draft.content,
        status=draft.status,
        revision=draft.revision,
        created_by=draft.created_by,
        updated_by=draft.updated_by,
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
    )


@onboarding_router.get(
    "/processes/{process_id}/contract/export",
    response_class=PlainTextResponse,
)
async def export_contract_draft(
    process_id: UUID,
    _admin: AdminUserDep,
    onboarding_service: OnboardingServiceDep,
):
    """Export the contract draft as plain text download."""
    draft = await onboarding_service.get_contract_draft(process_id)
    return PlainTextResponse(
        content=draft.content or "",
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=contract-{process_id}.txt",
        },
    )
