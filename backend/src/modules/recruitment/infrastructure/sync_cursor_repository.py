"""Repository for CalendarSyncCursor entity persistence.

Provides async database access for retrieving and upserting the calendar
sync token (sync_token + page_token) for the Organization singleton.
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.recruitment.domain.entities import CalendarSyncCursor


class CalendarSyncCursorRepository:
    """Handles CalendarSyncCursor persistence using async SQLAlchemy sessions.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: An SQLAlchemy AsyncSession instance for database operations.
        """
        self.session = session

    async def get_cursor(self) -> CalendarSyncCursor | None:
        """Retrieve the calendar sync cursor for the Organization singleton.

        Returns:
            The CalendarSyncCursor entity if found, None otherwise.
        """
        statement = select(CalendarSyncCursor).where(
            CalendarSyncCursor.organization_singleton_key == "default"
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def upsert_cursor(
        self,
        *,
        sync_token: str | None = None,
        page_token: str | None = None,
    ) -> CalendarSyncCursor:
        """Create or update the calendar sync cursor for the Organization.

        Updates sync_token and/or page_token and the last_sync_at timestamp.
        This ensures the unique constraint on organization_singleton_key is
        respected.

        Args:
            sync_token: The next sync token from Google Calendar, or None
                to clear it (on 410 GONE).
            page_token: The next page token for pagination, or None.

        Returns:
            The created or updated CalendarSyncCursor entity.
        """
        now = datetime.now(UTC)

        statement = select(CalendarSyncCursor).where(
            CalendarSyncCursor.organization_singleton_key == "default"
        )
        result = await self.session.execute(statement)
        cursor = result.scalars().first()

        if cursor is not None:
            if sync_token is not None:
                cursor.sync_token = sync_token
            cursor.page_token = page_token
            cursor.last_sync_at = now
            cursor.updated_at = now
            self.session.add(cursor)
            await self.session.flush()
            return cursor

        cursor = CalendarSyncCursor(
            organization_singleton_key="default",
            sync_token=sync_token,
            page_token=page_token,
            last_sync_at=now,
        )
        self.session.add(cursor)
        await self.session.flush()
        return cursor

    async def clear_sync_token(self) -> None:
        """Clear the sync token after a 410 GONE response.

        The page_token is also cleared. The cursor record itself is kept
        so the next sync starts from a bounded full sync.
        """
        cursor = await self.get_cursor()
        if cursor is not None:
            cursor.sync_token = None
            cursor.page_token = None
            cursor.last_sync_at = datetime.now(UTC)
            cursor.updated_at = datetime.now(UTC)
            self.session.add(cursor)
            await self.session.flush()
