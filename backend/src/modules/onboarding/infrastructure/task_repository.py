"""Repository for OnboardingTask persistence.

Provides async database access for ``OnboardingTask`` entities using
SQLAlchemy async sessions with SQLModel, following the patterns established in
the recruitment and employee modules.

The repository participates in the caller's transaction: it issues
``add``/``add_all`` and ``flush`` so generated fields are populated and the
changes are visible within the session, but it does not commit. The owning
service is responsible for committing (or rolling back) the transaction so that
checklist creation, task completion, and the audit write stay atomic.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.onboarding.domain.entities import OnboardingTask
from src.modules.onboarding.domain.enums import OnboardingTaskStatus


class OnboardingTaskRepository:
    """Handles OnboardingTask persistence using async SQLAlchemy sessions.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: An SQLAlchemy AsyncSession instance for database operations.
        """
        self.session = session

    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        """Bulk-insert onboarding tasks (the fixed four-item checklist).

        Used when a new OnboardingProcess is created to persist its checklist
        in a single round-trip. The insert participates in the caller's
        transaction; the service owns the commit.

        Args:
            tasks: The OnboardingTask entities to persist.

        Returns:
            The persisted OnboardingTask entities with generated fields populated.
        """
        self.session.add_all(tasks)
        await self.session.flush()
        return tasks

    async def get_by_id(self, task_id: UUID) -> OnboardingTask | None:
        """Retrieve an onboarding task by its unique identifier.

        Args:
            task_id: The UUID primary key of the task.

        Returns:
            The OnboardingTask entity if found, None otherwise.
        """
        statement = select(OnboardingTask).where(OnboardingTask.id == task_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_by_process(self, process_id: UUID) -> list[OnboardingTask]:
        """Retrieve all tasks for a process, ordered by their checklist order.

        Args:
            process_id: The UUID of the owning OnboardingProcess.

        Returns:
            A list of OnboardingTask entities ordered by ``order_index`` ascending.
        """
        statement = (
            select(OnboardingTask)
            .where(OnboardingTask.process_id == process_id)
            .order_by(OnboardingTask.order_index)  # type: ignore[arg-type]
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def set_status(
        self,
        task: OnboardingTask,
        status: OnboardingTaskStatus,
        completed_at: datetime | None = None,
        completed_by_user_id: UUID | None = None,
    ) -> OnboardingTask:
        """Update a task's status and completion metadata.

        The completion metadata is set as provided by the caller: when marking
        a task ``done`` the service passes the completion timestamp and the
        acting HR user id; both default to ``None`` for other transitions. The
        update participates in the caller's transaction; the service owns the
        commit.

        Args:
            task: The OnboardingTask entity to update.
            status: The new task status (``pending`` or ``done``).
            completed_at: The timestamp at which the task was completed, if any.
            completed_by_user_id: The id of the HR user who completed the task,
                if any.

        Returns:
            The updated OnboardingTask entity.
        """
        task.status = status.value
        task.completed_at = completed_at
        task.completed_by_user_id = completed_by_user_id
        self.session.add(task)
        await self.session.flush()
        return task

    async def count_by_status(self, process_id: UUID) -> dict[str, int]:
        """Count a process's tasks grouped by status.

        Supports the activation check: every task is done when the process has
        at least one task and the ``done`` count equals the total. Callers can
        derive ``total = sum(counts.values())`` and
        ``done = counts.get(OnboardingTaskStatus.DONE, 0)``. Statuses with no
        tasks are absent from the mapping (a process with zero tasks yields an
        empty dict).

        Args:
            process_id: The UUID of the owning OnboardingProcess.

        Returns:
            A mapping of status value to the number of tasks with that status.
        """
        statement = (
            select(OnboardingTask.status, func.count())
            .where(OnboardingTask.process_id == process_id)
            .group_by(OnboardingTask.status)
        )
        result = await self.session.execute(statement)
        return {str(status): int(count) for status, count in result.all()}

    async def count_by_status_for_processes(
        self, process_ids: list[UUID]
    ) -> dict[UUID, dict[str, int]]:
        """Count tasks grouped by process ID and status.

        Allows bulk fetching of status counts for multiple processes in a single
        query, avoiding N+1 issues when listing processes.

        Args:
            process_ids: A list of process UUIDs to fetch counts for.

        Returns:
            A dictionary mapping process UUID to a dict of status strings to integer counts.
        """
        if not process_ids:
            return {}

        statement = (
            select(OnboardingTask.process_id, OnboardingTask.status, func.count())
            .where(OnboardingTask.process_id.in_(process_ids))  # type: ignore[attr-defined]
            .group_by(OnboardingTask.process_id, OnboardingTask.status)  # type: ignore[arg-type]
        )
        result = await self.session.execute(statement)

        counts_by_process: dict[UUID, dict[str, int]] = {pid: {} for pid in process_ids}
        for process_id, status, count in result.all():
            counts_by_process[process_id][str(status)] = int(count)

        return counts_by_process
