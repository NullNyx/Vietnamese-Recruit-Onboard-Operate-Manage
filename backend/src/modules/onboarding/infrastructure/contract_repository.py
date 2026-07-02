"""Repository for OnboardingContractDraft persistence.

Provides async database access for onboarding contract drafts using
SQLAlchemy async sessions with SQLModel.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.onboarding.domain.entities import OnboardingContractDraft


class OnboardingContractRepository:
    """Handles OnboardingContractDraft persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_process(self, process_id: UUID) -> OnboardingContractDraft | None:
        """Retrieve contract draft for an onboarding process.

        Args:
            process_id: The onboarding process UUID.

        Returns:
            The OnboardingContractDraft if one exists, None otherwise.
        """
        statement = select(OnboardingContractDraft).where(
            OnboardingContractDraft.process_id == process_id
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create(self, draft: OnboardingContractDraft) -> OnboardingContractDraft:
        """Persist a new contract draft.

        Args:
            draft: The OnboardingContractDraft entity to persist.

        Returns:
            The persisted entity with generated fields populated.
        """
        self.session.add(draft)
        await self.session.flush()
        return draft

    async def update(self, draft: OnboardingContractDraft) -> OnboardingContractDraft:
        """Persist changes to an existing contract draft.

        Args:
            draft: The draft entity with updated fields.

        Returns:
            The updated entity.
        """
        self.session.add(draft)
        await self.session.flush()
        return draft
