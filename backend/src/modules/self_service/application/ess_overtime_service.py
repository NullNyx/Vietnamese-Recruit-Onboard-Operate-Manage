"""Employee Self-Service overtime request management.

Provides employee-facing overtime operations with ownership enforcement,
date validation, and planned hours validation. Delegates to the existing
OvertimeRepository for persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.modules.attendance.domain.entities import OvertimeRequest
from src.modules.attendance.domain.enums import OvertimeStatus
from src.modules.self_service.api.schemas import ESSOvertimeRequestCreate


class ESSOvertimeService:
    """Manages overtime requests for the authenticated employee.

    All operations enforce ownership — the employee can only interact
    with their own overtime requests.

    Args:
        session: Async database session for queries and mutations.
    """

    # Validation constants
    MIN_PLANNED_HOURS = Decimal("0.5")
    MAX_PLANNED_HOURS = Decimal("4.0")

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_requests(self, employee_id: UUID) -> list[OvertimeRequest]:
        """Return all overtime requests for the authenticated employee.

        Args:
            employee_id: The authenticated employee's ID.

        Returns:
            List of overtime requests ordered by creation date descending.
        """
        stmt = (
            select(OvertimeRequest)
            .where(OvertimeRequest.employee_id == employee_id)
            .order_by(col(OvertimeRequest.created_at).desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_request(
        self, employee_id: UUID, data: ESSOvertimeRequestCreate
    ) -> OvertimeRequest:
        """Create a new overtime request for the authenticated employee.

        Validates:
        - work_date is not in the past (today is allowed)
        - planned_hours is between 0.5 and 4.0

        Args:
            employee_id: The authenticated employee's ID.
            data: Validated request data (work_date, planned_hours, reason).

        Returns:
            The newly created overtime request with status "pending".

        Raises:
            HTTPException: 422 if work_date is in the past or planned_hours
                is outside the valid range.
        """
        today = datetime.now(timezone.utc).date()

        # Validate work_date is not in the past
        if data.work_date < today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_WORK_DATE",
                    "message": "Work date cannot be in the past",
                },
            )

        # Defense-in-depth: validate planned_hours range
        # (Pydantic schema already validates, but service layer double-checks)
        if data.planned_hours < self.MIN_PLANNED_HOURS or data.planned_hours > self.MAX_PLANNED_HOURS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_PLANNED_HOURS",
                    "message": "Planned hours must be between 0.5 and 4.0",
                },
            )

        request = OvertimeRequest(
            employee_id=employee_id,
            work_date=data.work_date,
            planned_hours=data.planned_hours,
            reason=data.reason,
            status=OvertimeStatus.PENDING,
        )

        self._session.add(request)
        await self._session.flush()
        await self._session.refresh(request)
        await self._session.commit()
        return request

    async def cancel_request(
        self, employee_id: UUID, request_id: UUID
    ) -> OvertimeRequest:
        """Cancel a pending overtime request owned by the employee.

        Validates:
        - The request exists and belongs to the authenticated employee
        - The request status is "pending"

        Args:
            employee_id: The authenticated employee's ID.
            request_id: The overtime request to cancel.

        Returns:
            The updated overtime request with status "cancelled".

        Raises:
            HTTPException: 403 if the request doesn't belong to the employee.
            HTTPException: 409 if the request is not in "pending" status.
        """
        stmt = select(OvertimeRequest).where(OvertimeRequest.id == request_id)
        result = await self._session.execute(stmt)
        request = result.scalars().first()

        if request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "OVERTIME_REQUEST_NOT_FOUND",
                    "message": f"Overtime request {request_id} not found",
                },
            )

        # Verify ownership
        if request.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "RESOURCE_FORBIDDEN",
                    "message": "You do not have access to this resource",
                },
            )

        # Verify status is pending
        if request.status != OvertimeStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "INVALID_STATUS_TRANSITION",
                    "message": f"Cannot cancel request with status '{request.status}'",
                },
            )

        request.status = "cancelled"
        self._session.add(request)
        await self._session.flush()
        await self._session.refresh(request)
        await self._session.commit()
        return request
