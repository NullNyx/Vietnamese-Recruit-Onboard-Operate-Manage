"""Repository for OnboardingProcess persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.onboarding.domain.entities import OnboardingProcess
from src.modules.onboarding.domain.enums import OnboardingStatus


class OnboardingRepository:
    """CRUD operations for OnboardingProcess."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, process: OnboardingProcess) -> OnboardingProcess:
        """Persist a new onboarding process."""
        self._session.add(process)
        await self._session.flush()
        return process

    async def get_by_candidate_id(self, candidate_id: str) -> OnboardingProcess | None:
        """Find an onboarding process by candidate ID."""
        statement = select(OnboardingProcess).where(OnboardingProcess.candidate_id == candidate_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, process_id: str) -> OnboardingProcess | None:
        """Find an onboarding process by ID."""
        statement = select(OnboardingProcess).where(OnboardingProcess.id == process_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[OnboardingProcess]:
        """List onboarding processes with pagination."""
        statement = (
            select(OnboardingProcess)
            .order_by(OnboardingProcess.created_at.desc())  # type: ignore[attr-defined]
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total onboarding processes."""
        from sqlalchemy import func

        statement = select(func.count()).select_from(OnboardingProcess)
        result = await self._session.execute(statement)
        return result.scalar_one()

    async def update_status(
        self,
        process: OnboardingProcess,
        status: str,
        notes: str | None = None,
    ) -> OnboardingProcess:
        """Update an onboarding process status."""
        process.status = status
        process.updated_at = datetime.now(UTC)
        if status == OnboardingStatus.COMPLETE.value:
            process.completed_at = datetime.now(UTC)
        if notes:
            process.notes = notes
        self._session.add(process)
        await self._session.flush()
        return process
