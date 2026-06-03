"""Repository for OnboardingProcess persistence.

Provides async database access for the ``OnboardingProcess`` entity using
SQLAlchemy async sessions with SQLModel, following the same patterns as the
recruitment and employee module repositories.

All methods participate in the caller's transaction: writes ``flush`` to the
session (so generated fields are populated and constraint violations surface
early) but never ``commit``. The service / consumer layer owns the transaction
boundary, which is essential to the atomic, single-transaction creation flow
described in the design (``start_from_event`` creates the employee, process,
checklist, and audit entry together, committing once).
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.onboarding.domain.entities import OnboardingProcess
from src.modules.onboarding.domain.enums import OnboardingStatus


class OnboardingProcessRepository:
    """Handles OnboardingProcess persistence using async SQLAlchemy sessions.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: An SQLAlchemy AsyncSession instance for database operations.
        """
        self.session = session

    async def create(self, process: OnboardingProcess) -> OnboardingProcess:
        """Persist a new onboarding process to the database.

        Adds the entity to the session and flushes so generated fields are
        populated and the ``candidate_id`` unique constraint is enforced
        immediately, but does not commit; the caller owns the transaction.

        Args:
            process: The OnboardingProcess entity to create.

        Returns:
            The persisted OnboardingProcess entity with generated fields populated.
        """
        self.session.add(process)
        await self.session.flush()
        return process

    async def counts_by_status(self) -> dict[str, int]:
        """Count processes grouped by status.

        Returns a mapping of status value to count for each status that has
        at least one process.  Used by the badge-count endpoint so the
        frontend can display accurate per-tab totals without loading items.

        Returns:
            A dict mapping status string to its process count.
        """
        statement = select(OnboardingProcess.status, func.count()).group_by(
            OnboardingProcess.status
        )
        result = await self.session.execute(statement)
        return {str(status): int(count) for status, count in result.all()}

    async def get_by_id(self, process_id: UUID) -> OnboardingProcess | None:
        """Retrieve an onboarding process by its unique identifier.

        Args:
            process_id: The UUID primary key of the onboarding process.

        Returns:
            The OnboardingProcess entity if found, None otherwise.
        """
        statement = select(OnboardingProcess).where(OnboardingProcess.id == process_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_by_candidate_id(self, candidate_id: UUID) -> OnboardingProcess | None:
        """Retrieve an onboarding process by its originating candidate id.

        This is the idempotency guard for event consumption: if a process
        already exists for the candidate, the consumer must leave it unchanged
        and create no additional process or employee record.

        Args:
            candidate_id: The UUID of the originating candidate.

        Returns:
            The existing OnboardingProcess for the candidate if one exists,
            None otherwise.
        """
        statement = select(OnboardingProcess).where(OnboardingProcess.candidate_id == candidate_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list(
        self,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[OnboardingProcess], int]:
        """Retrieve a paginated list of onboarding processes.

        Results are ordered by ``created_at`` descending. When a ``status``
        filter is supplied, only processes whose status is identical to it are
        returned. The returned total is the true count of processes matching
        the request (ignoring pagination), so callers can report accurate
        totals even when a page is empty.

        Args:
            status: Optional status value to filter by. When None, processes of
                every status are returned.
            page: The page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            A tuple of (list of OnboardingProcess entities for the page, total
            count of matching processes).
        """
        statement = select(OnboardingProcess)
        count_statement = select(func.count()).select_from(OnboardingProcess)

        if status is not None:
            statement = statement.where(OnboardingProcess.status == status)
            count_statement = count_statement.where(OnboardingProcess.status == status)

        count_result = await self.session.execute(count_statement)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        statement = statement.order_by(desc(OnboardingProcess.created_at))  # type: ignore[arg-type]
        statement = statement.offset(offset).limit(page_size)

        result = await self.session.execute(statement)
        processes = list(result.scalars().all())

        return processes, total

    async def get_for_update(self, process_id: UUID) -> OnboardingProcess | None:
        """Retrieve an onboarding process with a row-level lock.

        Issues ``SELECT ... FOR UPDATE`` so concurrent task-completion
        transactions on the same process are serialized. This is required for
        the atomic completion + activation flow: marking the last task done,
        completing the process, and activating the employee must not race.

        Must be called inside a transaction; the lock is held until the
        caller's transaction commits or rolls back.

        Args:
            process_id: The UUID primary key of the onboarding process.

        Returns:
            The locked OnboardingProcess entity if found, None otherwise.
        """
        statement = (
            select(OnboardingProcess).where(OnboardingProcess.id == process_id).with_for_update()
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def set_status(self, process: OnboardingProcess, status: str) -> OnboardingProcess:
        """Update an onboarding process status and bump its timestamps.

        Sets the process status, refreshes ``updated_at``, and — when the
        process transitions to ``complete`` — stamps ``completed_at`` with the
        current time. Flushes but does not commit; the caller owns the
        transaction so the status change rolls back with the rest of the
        activation work on any failure.

        Args:
            process: The OnboardingProcess entity to update (typically one
                already locked via ``get_for_update``).
            status: The new status value to apply.

        Returns:
            The updated OnboardingProcess entity.
        """
        now = datetime.now(UTC)
        process.status = status
        process.updated_at = now
        if status == OnboardingStatus.COMPLETE:
            process.completed_at = now
        self.session.add(process)
        await self.session.flush()
        return process
