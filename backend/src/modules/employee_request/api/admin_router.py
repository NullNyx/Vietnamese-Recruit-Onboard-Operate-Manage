"""FastAPI router for HR admin review of Employee Requests.

All endpoints require HR (admin) authentication.
Provides review queue listing, approve, and reject operations.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.modules.employee_request.application.review_service import (
    EmployeeRequestReviewService,
)
from src.modules.employee_request.container import (
    get_employee_request_repository,
    get_employee_request_review_service,
)
from src.modules.employee_request.infrastructure.employee_request_repository import (
    EmployeeRequestRepository,
)
from src.modules.identity.api.admin_router import AdminUserDep

admin_employee_request_router = APIRouter(
    prefix="/api/admin/employee-requests",
    tags=["admin", "employee-requests"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AdminEmployeeRequestItem(BaseModel):
    """List item for HR review queue."""

    id: UUID
    employee_id: UUID
    employee_name: str = ""
    request_type: str
    status: str
    submitted_at: str | None = None
    updated_at: str | None = None
    reason: str | None = None
    # Overtime fields
    work_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_minutes: int | None = None
    # Leave fields
    leave_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    # Cancellation
    cancellation_reason: str | None = None

    model_config = {"from_attributes": True}


class AdminReviewQueueResponse(BaseModel):
    """Response schema for the HR review queue."""

    requests: list[AdminEmployeeRequestItem]


class ReviewRequest(BaseModel):
    """Shared request schema for approve/reject."""

    review_reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Reason for the review decision",
    )


class ReviewResponse(BaseModel):
    """Response schema for approve/reject actions."""

    message: str
    request: AdminEmployeeRequestItem


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@admin_employee_request_router.get(
    "",
    response_model=AdminReviewQueueResponse,
)
async def list_review_queue(
    admin_user: AdminUserDep,
    repo: EmployeeRequestRepository = Depends(get_employee_request_repository),
) -> AdminReviewQueueResponse:
    """List all submitted employee requests for HR review.

    Returns requests newest first with employee name.
    """
    submitted = await repo.get_all_submitted()
    items = []
    for sw in submitted:
        item = AdminEmployeeRequestItem(
            **sw.request.model_dump(),
            employee_name=sw.employee_name,
        )
        items.append(item)
    return AdminReviewQueueResponse(requests=items)


@admin_employee_request_router.post(
    "/{request_id}/approve",
    response_model=ReviewResponse,
)
async def approve_request(
    request_id: UUID,
    body: ReviewRequest,
    admin_user: AdminUserDep,
    review_service: EmployeeRequestReviewService = Depends(
        get_employee_request_review_service,
    ),
) -> ReviewResponse:
    """Approve a submitted employee request."""
    updated = await review_service.approve_request(
        request_id=request_id,
        admin_user=admin_user,
        review_reason=body.review_reason,
    )
    return ReviewResponse(
        message="Request approved",
        request=AdminEmployeeRequestItem.model_validate(updated),
    )


@admin_employee_request_router.post(
    "/{request_id}/reject",
    response_model=ReviewResponse,
)
async def reject_request(
    request_id: UUID,
    body: ReviewRequest,
    admin_user: AdminUserDep,
    review_service: EmployeeRequestReviewService = Depends(
        get_employee_request_review_service,
    ),
) -> ReviewResponse:
    """Reject a submitted employee request."""
    updated = await review_service.reject_request(
        request_id=request_id,
        admin_user=admin_user,
        review_reason=body.review_reason,
    )
    return ReviewResponse(
        message="Request rejected",
        request=AdminEmployeeRequestItem.model_validate(updated),
    )
