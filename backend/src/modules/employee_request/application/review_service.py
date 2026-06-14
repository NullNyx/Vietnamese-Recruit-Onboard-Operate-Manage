"""Application service for HR review of Employee Requests.

Handles approve and reject actions on submitted requests.
Review logic is shared across leave and overtime types.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.modules.employee_request.domain.entities import EmployeeRequest
from src.modules.employee_request.domain.enums import RequestStatus
from src.modules.employee_request.domain.exceptions import (
    RequestNotFoundError,
    RequestNotReviewableError,
)
from src.modules.employee_request.infrastructure.employee_request_repository import (
    EmployeeRequestRepository,
)
from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.domain.entities import AuditActionType, User


class EmployeeRequestReviewService:
    """Service for HR review of employee requests.

    Provides approve and reject operations with audit logging.
    Both leave and overtime requests use the same review logic.

    Attributes:
        repo: The employee request repository.
        audit_service: The audit service for recording review actions.
    """

    def __init__(
        self,
        repo: EmployeeRequestRepository,
        audit_service: AuditService,
    ) -> None:
        self.repo = repo
        self.audit_service = audit_service

    async def approve_request(
        self,
        request_id: UUID,
        admin_user: User,
        review_reason: str | None = None,
    ) -> EmployeeRequest:
        """Approve a submitted employee request.

        Uses row-level lock to prevent concurrent HR reviewers from
        processing the same request. Re-checks the status after
        acquiring the lock before applying the update.

        Args:
            request_id: The UUID of the request to approve.
            admin_user: The admin User performing the approval.
            review_reason: Optional reason for the approval decision.

        Returns:
            The updated EmployeeRequest with APPROVED status.

        Raises:
            RequestNotFoundError: If the request does not exist.
            RequestNotReviewableError: If the request is not SUBMITTED.
        """
        request = await self.repo.get_by_id_with_lock(request_id)
        if request is None:
            raise RequestNotFoundError(request_id)

        if request.status != RequestStatus.SUBMITTED:
            raise RequestNotReviewableError(request_id, request.status.value)

        now = datetime.now(UTC)
        request.status = RequestStatus.APPROVED
        request.reviewed_by_user_id = admin_user.id
        request.reviewed_at = now
        request.review_reason = review_reason
        request.updated_at = now

        updated = await self.repo.update(request)

        await self.audit_service.log_action(
            admin=admin_user,
            action_type=AuditActionType.REQUEST_APPROVE,
            details={
                "request_id": str(request_id),
                "employee_id": str(request.employee_id),
                "request_type": request.request_type.value,
                "review_reason": review_reason,
            },
        )

        return updated

    async def reject_request(
        self,
        request_id: UUID,
        admin_user: User,
        review_reason: str | None = None,
    ) -> EmployeeRequest:
        """Reject a submitted employee request.

        Uses row-level lock to prevent concurrent HR reviewers from
        processing the same request. Re-checks the status after
        acquiring the lock before applying the update.

        Args:
            request_id: The UUID of the request to reject.
            admin_user: The admin User performing the rejection.
            review_reason: Optional reason for the rejection decision.

        Returns:
            The updated EmployeeRequest with REJECTED status.

        Raises:
            RequestNotFoundError: If the request does not exist.
            RequestNotReviewableError: If the request is not SUBMITTED.
        """
        if not review_reason or not review_reason.strip():
            raise ValueError('Rejection reason (decision_reason) is required')

        request = await self.repo.get_by_id_with_lock(request_id)
        if request is None:
            raise RequestNotFoundError(request_id)

        if request.status != RequestStatus.SUBMITTED:
            raise RequestNotReviewableError(request_id, request.status.value)

        now = datetime.now(UTC)
        request.status = RequestStatus.REJECTED
        request.reviewed_by_user_id = admin_user.id
        request.reviewed_at = now
        request.review_reason = review_reason
        request.updated_at = now

        updated = await self.repo.update(request)

        await self.audit_service.log_action(
            admin=admin_user,
            action_type=AuditActionType.REQUEST_REJECT,
            details={
                "request_id": str(request_id),
                "employee_id": str(request.employee_id),
                "request_type": request.request_type.value,
                "review_reason": review_reason,
            },
        )

        return updated
