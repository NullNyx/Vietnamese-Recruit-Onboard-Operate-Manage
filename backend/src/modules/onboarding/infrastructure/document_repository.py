"""Repository for OnboardingDocument persistence.

Provides async database access for onboarding document items using
SQLAlchemy async sessions with SQLModel.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.onboarding.domain.entities import OnboardingDocument

class OnboardingDocumentRepository:
    """Handles OnboardingDocument persistence using async SQLAlchemy sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(self, docs: list[OnboardingDocument]) -> list[OnboardingDocument]:
        """Bulk-insert onboarding document items."""
        self.session.add_all(docs)
        await self.session.flush()
        return docs

    async def list_by_process(self, process_id: UUID) -> list[OnboardingDocument]:
        """Retrieve all document items for a process, ordered by document_type."""
        statement = (
            select(OnboardingDocument)
            .where(OnboardingDocument.process_id == process_id)
            .order_by(OnboardingDocument.document_type)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, doc_id: UUID) -> OnboardingDocument | None:
        """Retrieve a document item by its unique identifier."""
        statement = select(OnboardingDocument).where(OnboardingDocument.id == doc_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def update(self, doc: OnboardingDocument) -> OnboardingDocument:
        """Persist changes to a document item."""
        self.session.add(doc)
        await self.session.flush()
        return doc
