"""FastAPI router for Employee Self-Service document endpoints.

Provides endpoints for employees to list their personal documents
and generate pre-signed download URLs. All endpoints enforce ownership
via the rate-limited employee_id dependency.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.employee.infrastructure.document_repository import (
    DocumentRepository,
)
from src.modules.employee.infrastructure.minio_client import MinIOClient
from src.modules.employee.container import get_document_repository, get_minio_client
from src.modules.identity.container import get_db_session
from src.modules.self_service.api.rate_limiter import check_ess_rate_limit
from src.modules.self_service.api.schemas import ESSDocumentResponse

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

EmployeeIdDep = Annotated[UUID, Depends(check_ess_rate_limit)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

document_router = APIRouter(prefix="/documents", tags=["ess-documents"])


@document_router.get("", response_model=list[ESSDocumentResponse])
async def list_documents(
    employee_id: EmployeeIdDep,
    document_repo: DocumentRepository = Depends(get_document_repository),
    document_type: str | None = Query(None, description="Filter by document type"),
) -> list[ESSDocumentResponse]:
    """List all documents for the authenticated employee.

    Returns documents associated with the employee, optionally filtered
    by document_type. Only documents owned by the authenticated employee
    are returned (ownership enforced via employee_id from token).

    Requirements: 9.1, 9.4
    """
    documents = await document_repo.list_by_employee(employee_id)

    # Apply document_type filter if provided
    if document_type:
        documents = [
            doc for doc in documents if doc.document_type == document_type
        ]

    return [
        ESSDocumentResponse(
            id=doc.id,  # type: ignore[arg-type]
            file_name=doc.file_name,
            document_type=doc.document_type,
            file_size=doc.file_size,
            uploaded_at=doc.uploaded_at,
        )
        for doc in documents
    ]


@document_router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    employee_id: EmployeeIdDep,
    document_repo: DocumentRepository = Depends(get_document_repository),
    minio_client: MinIOClient = Depends(get_minio_client),
) -> dict[str, str]:
    """Generate a pre-signed download URL for a document.

    Verifies that the document belongs to the authenticated employee
    before generating a MinIO pre-signed URL valid for 15 minutes.

    Requirements: 9.2, 9.3
    """
    # Fetch the document
    document = await document_repo.get_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document {document_id} not found",
            },
        )

    # Verify ownership — reject access to other employee's documents
    if document.employee_id != employee_id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "RESOURCE_FORBIDDEN",
                "message": "You do not have access to this document",
            },
        )

    # Generate pre-signed URL (15-minute expiry = 900 seconds)
    try:
        presigned_url = await minio_client.generate_presigned_url(
            document.storage_path, expires_seconds=900
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "Document file not found in storage",
            },
        )
    except OSError:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "STORAGE_UNAVAILABLE",
                "message": "Document storage service is temporarily unavailable. Please try again later.",
            },
            headers={"Retry-After": "30"},
        )

    return {
        "download_url": presigned_url,
        "file_name": document.file_name,
        "expires_in_seconds": "900",
    }
