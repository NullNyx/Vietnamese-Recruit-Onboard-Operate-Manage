"""Repository for EmployeeRequest entity CRUD operations.

Provides async database access for employee requests using SQLAlchemy
async sessions with SQLModel.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.employee.domain.entities import Employee  # noqa: F401
from src.modules.employee_request.domain.entities import EmployeeRequest
from src.modules.employee_request.domain.enums import RequestStatus, RequestType


@dataclass(frozen=True)
class SubmittedRequestWithEmployee:
    """An employee request enriched with the submitting employee's full name."""

    request: EmployeeRequest
    employee_name: str


class EmployeeRequestRepository:
    """Handles EmployeeRequest persistence.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, request: EmployeeRequest) -> EmployeeRequest:
        """Persist a new employee request.

        Args:
            request: The EmployeeRequest to create.

        Returns:
            The created EmployeeRequest with generated fields populated.
        """
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def get_by_id(self, request_id: UUID) -> EmployeeRequest | None:
        """Retrieve a request by its ID.

        Args:
            request_id: The UUID of the request.

        Returns:
            The EmployeeRequest if found, None otherwise.
        """
        statement = select(EmployeeRequest).where(EmployeeRequest.id == request_id)  # type: ignore[arg-type]
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_employee_id(self, employee_id: UUID) -> list[EmployeeRequest]:
        """List all requests for an employee (newest first).

        Args:
            employee_id: The UUID of the employee.

        Returns:
            List of EmployeeRequest objects.
        """
        statement = (
            select(EmployeeRequest)
            .where(EmployeeRequest.employee_id == employee_id)  # type: ignore[arg-type]
            .order_by(EmployeeRequest.submitted_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_overlapping_overtime(
        self,
        employee_id: UUID,
        work_date: date,
        exclude_id: UUID | None = None,
    ) -> list[EmployeeRequest]:
        """Find submitted or approved overtime requests on the same date.

        Args:
            employee_id: The UUID of the employee.
            work_date: The work date to check for overlap.
            exclude_id: Optional request ID to exclude (for updates).

        Returns:
            List of overlapping EmployeeRequest objects.
        """
        statement = select(EmployeeRequest).where(
            EmployeeRequest.employee_id == employee_id,  # type: ignore[arg-type]
            EmployeeRequest.request_type == RequestType.OVERTIME,  # type: ignore[arg-type]
            EmployeeRequest.work_date == work_date,  # type: ignore[arg-type]
            EmployeeRequest.status.in_(  # type: ignore[arg-type]
                [RequestStatus.SUBMITTED, RequestStatus.APPROVED],
            ),
        )
        if exclude_id is not None:
            statement = statement.where(EmployeeRequest.id != exclude_id)  # type: ignore[arg-type]

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_overlapping_leave(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
        exclude_id: UUID | None = None,
    ) -> list[EmployeeRequest]:
        """Find submitted or approved leave requests overlapping the date range.

        Two ranges overlap when one's start <= other's end AND other's
        start <= one's end.

        Args:
            employee_id: The UUID of the employee.
            start_date: Start of the leave range.
            end_date: End of the leave range.
            exclude_id: Optional request ID to exclude (for updates).

        Returns:
            List of overlapping EmployeeRequest objects.
        """
        statement = select(EmployeeRequest).where(
            EmployeeRequest.employee_id == employee_id,  # type: ignore[arg-type]
            EmployeeRequest.request_type == RequestType.LEAVE,  # type: ignore[arg-type]
            EmployeeRequest.start_date <= end_date,  # type: ignore[arg-type]
            EmployeeRequest.end_date >= start_date,  # type: ignore[arg-type]
            EmployeeRequest.status.in_(  # type: ignore[arg-type]
                [RequestStatus.SUBMITTED, RequestStatus.APPROVED],
            ),
        )
        if exclude_id is not None:
            statement = statement.where(EmployeeRequest.id != exclude_id)  # type: ignore[arg-type]

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(self, request: EmployeeRequest) -> EmployeeRequest:
        """Update an existing employee request.

        Args:
            request: The EmployeeRequest with modifications applied.

        Returns:
            The updated EmployeeRequest.
        """
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def get_by_id_with_lock(self, request_id: UUID) -> EmployeeRequest | None:
        """Retrieve a request by its ID with row-level lock (FOR UPDATE).

        Use this in concurrent scenarios to prevent race conditions:
        two HR admins reviewing the same request simultaneously.

        Args:
            request_id: The UUID of the request.

        Returns:
            The EmployeeRequest if found, None otherwise.
        """
        statement = (
            select(EmployeeRequest)
            .where(EmployeeRequest.id == request_id)  # type: ignore[arg-type]
            .with_for_update()
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_submitted(self) -> list[SubmittedRequestWithEmployee]:
        """List all submitted requests with employee name, newest first.

        Joins with the employees table to include the submitting employee's
        full name for HR review display.

        Returns:
            List of SubmittedRequestWithEmployee objects.
        """
        statement = (
            select(EmployeeRequest, Employee.full_name)
            .join(Employee, EmployeeRequest.employee_id == Employee.id)  # type: ignore[arg-type]
            .where(EmployeeRequest.status == RequestStatus.SUBMITTED)  # type: ignore[arg-type]
            .order_by(EmployeeRequest.submitted_at.desc())
        )
        result = await self.session.execute(statement)
        rows = result.all()
        return [SubmittedRequestWithEmployee(request=req, employee_name=name) for req, name in rows]

    async def get_all_filtered(
        self,
        request_type: RequestType | None = None,
        status: RequestStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        employee_id: UUID | None = None,
    ) -> list[SubmittedRequestWithEmployee]:
        """List requests with optional filters, joined with employee name.

        Supports filtering by request type, status, date range, and employee.
        Results are ordered newest first by submitted_at.

        Args:
            request_type: Optional filter by request type (leave/overtime).
            status: Optional filter by status (submitted/approved/rejected/cancelled).
            date_from: Optional start date filter (submitted_at >= date_from).
            date_to: Optional end date filter (submitted_at <= date_to).
            employee_id: Optional filter by employee UUID.

        Returns:
            List of SubmittedRequestWithEmployee objects matching the filters.
        """
        statement = (
            select(EmployeeRequest, Employee.full_name)
            .join(Employee, EmployeeRequest.employee_id == Employee.id)  # type: ignore[arg-type]
            .order_by(EmployeeRequest.submitted_at.desc())
        )

        if request_type is not None:
            statement = statement.where(  # type: ignore[arg-type]
                EmployeeRequest.request_type == request_type,
            )
        if status is not None:
            statement = statement.where(  # type: ignore[arg-type]
                EmployeeRequest.status == status,
            )
        if date_from is not None:
            inclusive_start = datetime.combine(date_from, time.min)
            statement = statement.where(  # type: ignore[arg-type]
                EmployeeRequest.submitted_at >= inclusive_start,  # type: ignore[operator]
            )
        if date_to is not None:
            exclusive_end = datetime.combine(date_to + timedelta(days=1), time.min)
            statement = statement.where(  # type: ignore[arg-type]
                EmployeeRequest.submitted_at < exclusive_end,  # type: ignore[operator]
            )
        if employee_id is not None:
            statement = statement.where(  # type: ignore[arg-type]
                EmployeeRequest.employee_id == employee_id,
            )

        result = await self.session.execute(statement)
        rows = result.all()
        return [SubmittedRequestWithEmployee(request=req, employee_name=name) for req, name in rows]
