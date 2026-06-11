"""Application service for Leave Employee Requests.

Handles creation, cancellation, and querying of leave requests.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from src.modules.employee_request.domain.entities import EmployeeRequest
from src.modules.employee_request.domain.enums import LeaveType, RequestStatus, RequestType
from src.modules.employee_request.domain.exceptions import (
    LeaveEndBeforeStartError,
    LeaveOverlapError,
    RequestNotCancellableError,
    RequestNotFoundError,
    RequestNotOwnedByEmployeeError,
)
from src.modules.employee_request.infrastructure.employee_request_repository import (
    EmployeeRequestRepository,
)


class LeaveService:
    """Service for leave request operations.

    Attributes:
        repo: The employee request repository.
    """

    def __init__(self, repo: EmployeeRequestRepository) -> None:
        self.repo = repo

    async def create_leave(
        self,
        employee_id: UUID,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        reason: str,
    ) -> EmployeeRequest:
        """Create a new leave request.

        Args:
            employee_id: The submitting employee's UUID.
            leave_type: Type of leave (annual, sick, unpaid, other).
            start_date: First day of leave.
            end_date: Last day of leave (must be >= start_date).
            reason: Reason for leave.

        Returns:
            The created EmployeeRequest with SUBMITTED status.

        Raises:
            LeaveEndBeforeStartError: If end_date < start_date.
            LeaveOverlapError: If overlapping leave request exists.
        """
        if end_date < start_date:
            raise LeaveEndBeforeStartError()

        # Check overlap
        overlapping = await self.repo.find_overlapping_leave(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )
        if overlapping:
            raise LeaveOverlapError(start=start_date, end=end_date)

        now = datetime.now(UTC)
        request = EmployeeRequest(
            employee_id=employee_id,
            request_type=RequestType.LEAVE,
            status=RequestStatus.SUBMITTED,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            submitted_at=now,
            updated_at=now,
            created_at=now,
        )

        return await self.repo.create(request)

    async def cancel_leave(
        self,
        request_id: UUID,
        employee_id: UUID,
        cancellation_reason: str | None = None,
    ) -> EmployeeRequest:
        """Cancel a submitted leave request.

        Only the owning employee can cancel, and only if the request
        is SUBMITTED and of type LEAVE.

        Args:
            request_id: The UUID of the request to cancel.
            employee_id: The UUID of the requesting employee.
            cancellation_reason: Optional reason for cancellation.

        Returns:
            The cancelled EmployeeRequest.

        Raises:
            RequestNotFoundError: If request does not exist.
            RequestNotOwnedByEmployeeError: If employee does not own it.
            RequestNotCancellableError: If not SUBMITTED or not LEAVE type.
        """
        request = await self.repo.get_by_id(request_id)
        if request is None:
            raise RequestNotFoundError(request_id)

        if request.employee_id != employee_id:
            raise RequestNotOwnedByEmployeeError()

        if request.request_type != RequestType.LEAVE:
            raise RequestNotCancellableError()

        if request.status != RequestStatus.SUBMITTED:
            raise RequestNotCancellableError()

        request.status = RequestStatus.CANCELLED
        request.cancellation_reason = cancellation_reason
        request.updated_at = datetime.now(UTC)

        return await self.repo.update(request)

    async def list_my_leaves(self, employee_id: UUID) -> list[EmployeeRequest]:
        """List all leave requests for the current employee.

        Args:
            employee_id: The UUID of the employee.

        Returns:
            List of EmployeeRequest objects, newest first.
        """
        all_requests = await self.repo.get_by_employee_id(employee_id)
        return [r for r in all_requests if r.request_type == RequestType.LEAVE]
