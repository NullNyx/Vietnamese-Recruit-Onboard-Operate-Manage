"""Repository for EmployeeRequest entity CRUD operations.

Provides async database access for employee requests using SQLAlchemy
async sessions with SQLModel.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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
