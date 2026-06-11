"""Application service for Overtime Employee Requests.

Handles creation, cancellation, and querying of overtime requests.
HR review (approve/reject) is scoped for future work.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import UUID

from src.modules.employee_request.domain.entities import EmployeeRequest
from src.modules.employee_request.domain.enums import RequestStatus, RequestType
from src.modules.employee_request.domain.exceptions import (
    OvertimeEndBeforeStartError,
    OvertimeOverlapError,
    RequestNotCancellableError,
    RequestNotFoundError,
    RequestNotOwnedByEmployeeError,
)
from src.modules.employee_request.infrastructure.employee_request_repository import (
    EmployeeRequestRepository,
)


class OvertimeService:
    """Service for overtime request operations.

    Attributes:
        repo: The employee request repository.
    """

    def __init__(self, repo: EmployeeRequestRepository) -> None:
        self.repo = repo

    async def create_overtime(
        self,
        employee_id: UUID,
        work_date: date,
        start_time: time,
        end_time: time,
        reason: str,
        project_or_task: str | None = None,
    ) -> EmployeeRequest:
        """Create a new overtime request.

        Args:
            employee_id: The submitting employee's UUID.
            work_date: The date overtime is worked.
            start_time: Start time of overtime.
            end_time: End time of overtime (must be after start_time).
            reason: Reason for overtime.
            project_or_task: Optional project or task name.

        Returns:
            The created EmployeeRequest with SUBMITTED status.

        Raises:
            OvertimeEndBeforeStartError: If end_time <= start_time.
            OvertimeOverlapError: If overlapping request exists on same date.
        """
        if end_time <= start_time:
            raise OvertimeEndBeforeStartError()

        # Check overlap
        overlapping = await self.repo.find_overlapping_overtime(
            employee_id=employee_id,
            work_date=work_date,
        )
        if overlapping:
            raise OvertimeOverlapError(work_date=work_date)

        # Build request
        now = datetime.now(UTC)
        request = EmployeeRequest(
            employee_id=employee_id,
            request_type=RequestType.OVERTIME,
            status=RequestStatus.SUBMITTED,
            work_date=work_date,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
            project_or_task=project_or_task or None,
            submitted_at=now,
            updated_at=now,
            created_at=now,
        )
        # Derive duration (not user-entered)
        request.duration_minutes = request.derive_duration()

        return await self.repo.create(request)

    async def cancel_overtime(
        self,
        request_id: UUID,
        employee_id: UUID,
        cancellation_reason: str | None = None,
    ) -> EmployeeRequest:
        """Cancel a submitted overtime request.

        Only the owning employee can cancel, and only if the request
        is still in SUBMITTED status.

        Args:
            request_id: The UUID of the request to cancel.
            employee_id: The UUID of the requesting employee.
            cancellation_reason: Optional reason for cancellation.

        Returns:
            The cancelled EmployeeRequest.

        Raises:
            RequestNotFoundError: If request does not exist.
            RequestNotOwnedByEmployeeError: If employee does not own it.
            RequestNotCancellableError: If request is not SUBMITTED.
        """
        request = await self.repo.get_by_id(request_id)
        if request is None:
            raise RequestNotFoundError(request_id)

        if request.employee_id != employee_id:
            raise RequestNotOwnedByEmployeeError()

        if request.request_type != RequestType.OVERTIME:
            raise RequestNotCancellableError()

        if request.status != RequestStatus.SUBMITTED:
            raise RequestNotCancellableError()

        request.status = RequestStatus.CANCELLED
        request.cancellation_reason = cancellation_reason
        request.updated_at = datetime.now(UTC)

        return await self.repo.update(request)

    async def list_my_overtime(
        self,
        employee_id: UUID,
    ) -> list[EmployeeRequest]:
        """List all overtime requests for the current employee.

        Args:
            employee_id: The UUID of the employee.

        Returns:
            List of EmployeeRequest objects, newest first.
        """
        all_requests = await self.repo.get_by_employee_id(employee_id)
        return [r for r in all_requests if r.request_type == RequestType.OVERTIME]
