"""Employee Self-Service Leave Service.

Provides leave management operations for the authenticated employee:
viewing balances, listing requests, submitting new requests, and
cancelling pending requests. All operations enforce ownership via
the employee_id parameter extracted from the JWT token.
"""

from __future__ import annotations

from datetime import date, datetime, UTC
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.attendance.domain.entities import LeaveRequest
from src.modules.attendance.infrastructure.leave_repository import (
    LeaveBalanceRepository,
    LeaveRequestRepository,
    LeaveTypeRepository,
)
from src.modules.self_service.api.schemas import (
    ESSLeaveBalanceResponse,
    ESSLeaveRequestCreate,
    ESSLeaveRequestResponse,
)


class ESSLeaveService:
    """Self-service leave operations for employees.

    Wraps the existing leave repositories with ownership guards
    and ESS-specific validation rules (no past dates, balance checks).

    Args:
        balance_repo: Repository for leave balance queries.
        request_repo: Repository for leave request CRUD.
        type_repo: Repository for leave type lookups.
        session: Database session for transaction management.
    """

    def __init__(
        self,
        balance_repo: LeaveBalanceRepository,
        request_repo: LeaveRequestRepository,
        type_repo: LeaveTypeRepository,
        session: AsyncSession,
    ) -> None:
        self._balance_repo = balance_repo
        self._request_repo = request_repo
        self._type_repo = type_repo
        self._session = session

    async def get_balances(self, employee_id: UUID) -> list[ESSLeaveBalanceResponse]:
        """Return all leave type balances for the current year.

        Joins leave_balances with leave_types to include display names.

        Args:
            employee_id: The authenticated employee's UUID.

        Returns:
            List of leave balance responses with type names.
        """
        current_year = date.today().year
        balances = await self._balance_repo.get_by_employee_year(employee_id, current_year)

        # Build a map of leave_type_id -> display_name
        leave_types = await self._type_repo.list_all()
        type_map: dict[UUID, str] = {lt.id: lt.display_name for lt in leave_types}

        results: list[ESSLeaveBalanceResponse] = []
        for balance in balances:
            results.append(
                ESSLeaveBalanceResponse(
                    leave_type_id=balance.leave_type_id,
                    leave_type_name=type_map.get(balance.leave_type_id, "Unknown"),
                    total_days=balance.total_days,
                    used_days=balance.used_days,
                    remaining_days=balance.remaining_days,
                )
            )

        return results

    async def get_requests(self, employee_id: UUID) -> list[ESSLeaveRequestResponse]:
        """Return all leave requests for the authenticated employee.

        Joins leave_requests with leave_types for type display names.

        Args:
            employee_id: The authenticated employee's UUID.

        Returns:
            List of leave request responses.
        """
        requests, _ = await self._request_repo.list_by_employee(
            employee_id, page=1, page_size=1000
        )

        # Build a map of leave_type_id -> display_name
        leave_types = await self._type_repo.list_all()
        type_map: dict[UUID, str] = {lt.id: lt.display_name for lt in leave_types}

        results: list[ESSLeaveRequestResponse] = []
        for req in requests:
            results.append(
                ESSLeaveRequestResponse(
                    id=req.id,
                    leave_type_name=type_map.get(req.leave_type_id, "Unknown"),
                    start_date=req.start_date,
                    end_date=req.end_date,
                    total_days=req.total_days,
                    status=req.status,
                    reason=req.reason,
                    created_at=req.created_at,
                )
            )

        return results

    async def create_request(
        self, employee_id: UUID, data: ESSLeaveRequestCreate
    ) -> ESSLeaveRequestResponse:
        """Create a new leave request with validation.

        Validates:
        - start_date >= today (no past dates)
        - end_date >= start_date
        - Sufficient leave balance for the requested days

        Args:
            employee_id: The authenticated employee's UUID.
            data: The leave request creation payload.

        Returns:
            The created leave request response.

        Raises:
            HTTPException: 422 INVALID_DATE_RANGE if dates are invalid.
            HTTPException: 422 INSUFFICIENT_LEAVE_BALANCE if balance is insufficient.
        """
        today = date.today()

        # Validate start_date is not in the past
        if data.start_date < today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_DATE_RANGE",
                    "message": "Start date cannot be in the past",
                },
            )

        # Validate end_date >= start_date
        if data.end_date < data.start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_DATE_RANGE",
                    "message": "End date must be on or after start date",
                },
            )

        # Calculate total days (calendar days inclusive)
        total_days = Decimal(str((data.end_date - data.start_date).days + 1))

        # Check leave balance
        year = data.start_date.year
        balance = await self._balance_repo.get_balance(
            employee_id, data.leave_type_id, year
        )

        if balance is None or balance.remaining_days < total_days:
            remaining = Decimal("0") if balance is None else balance.remaining_days
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INSUFFICIENT_LEAVE_BALANCE",
                    "message": (
                        f"Insufficient leave balance: {remaining} days remaining, "
                        f"{total_days} requested"
                    ),
                },
            )

        # Create the leave request with status "pending"
        leave_request = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=data.leave_type_id,
            start_date=data.start_date,
            end_date=data.end_date,
            total_days=total_days,
            reason=data.reason,
            status="pending",
        )

        created = await self._request_repo.create(leave_request)
        await self._session.commit()

        # Resolve leave type name for response
        leave_type = await self._type_repo.get_by_id(data.leave_type_id)
        type_name = leave_type.display_name if leave_type else "Unknown"

        return ESSLeaveRequestResponse(
            id=created.id,
            leave_type_name=type_name,
            start_date=created.start_date,
            end_date=created.end_date,
            total_days=created.total_days,
            status=created.status,
            reason=created.reason,
            created_at=created.created_at,
        )

    async def cancel_request(
        self, employee_id: UUID, request_id: UUID
    ) -> ESSLeaveRequestResponse:
        """Cancel a pending leave request.

        Validates:
        - The request belongs to the authenticated employee (ownership)
        - The request status is "pending"

        Args:
            employee_id: The authenticated employee's UUID.
            request_id: The leave request UUID to cancel.

        Returns:
            The updated leave request response.

        Raises:
            HTTPException: 404 if request not found.
            HTTPException: 403 RESOURCE_FORBIDDEN if not owned by employee.
            HTTPException: 409 INVALID_STATUS_TRANSITION if not pending.
        """
        leave_request = await self._request_repo.get_by_id(request_id)

        if leave_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "LEAVE_REQUEST_NOT_FOUND",
                    "message": f"Leave request not found: {request_id}",
                },
            )

        # Verify ownership
        if leave_request.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "RESOURCE_FORBIDDEN",
                    "message": "You do not have permission to access this resource",
                },
            )

        # Verify status is pending
        if leave_request.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "INVALID_STATUS_TRANSITION",
                    "message": (
                        f"Cannot cancel a leave request with status '{leave_request.status}'. "
                        "Only pending requests can be cancelled."
                    ),
                },
            )

        # Update to cancelled
        leave_request.status = "cancelled"
        leave_request.updated_at = datetime.now(UTC)

        updated = await self._request_repo.update(leave_request)
        await self._session.commit()

        # Resolve leave type name for response
        leave_type = await self._type_repo.get_by_id(updated.leave_type_id)
        type_name = leave_type.display_name if leave_type else "Unknown"

        return ESSLeaveRequestResponse(
            id=updated.id,
            leave_type_name=type_name,
            start_date=updated.start_date,
            end_date=updated.end_date,
            total_days=updated.total_days,
            status=updated.status,
            reason=updated.reason,
            created_at=updated.created_at,
        )
