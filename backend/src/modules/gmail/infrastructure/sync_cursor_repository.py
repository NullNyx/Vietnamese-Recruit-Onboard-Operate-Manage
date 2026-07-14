"""Repository for SyncCursor entity persistence.

Provides async database access for the single Organization-scoped Gmail
synchronization cursor.
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.gmail.domain.entities import SyncCursor


class SyncCursorRepository:
    """Handles SyncCursor entity persistence using async SQLAlchemy sessions.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: An SQLAlchemy AsyncSession instance for database operations.
        """
        self.session = session

    async def get_cursor(self) -> SyncCursor | None:
        """Retrieve the Gmail cursor for the Organization singleton."""
        statement = select(SyncCursor).where(SyncCursor.organization_singleton_key == "default")
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def clear_cursor(self) -> None:
        """Clear the cursor so the next poll establishes a fresh baseline."""
        cursor = await self.get_cursor()
        if cursor is not None:
            await self.session.delete(cursor)
            await self.session.flush()

    async def upsert_cursor(self, history_id: str) -> SyncCursor:
        """Create or update the Organization-scoped Gmail cursor."""
        now = datetime.now(UTC)

        cursor = await self.get_cursor()
        if cursor is not None:
            cursor.history_id = history_id
            cursor.last_poll_at = now
            cursor.updated_at = now
            self.session.add(cursor)
            await self.session.flush()
            return cursor

        cursor = SyncCursor(
            organization_singleton_key="default",
            history_id=history_id,
            last_poll_at=now,
        )
        self.session.add(cursor)
        await self.session.flush()
        return cursor
