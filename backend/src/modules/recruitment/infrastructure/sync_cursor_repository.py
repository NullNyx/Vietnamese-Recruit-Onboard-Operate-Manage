"""Repository for CalendarSyncCursor entity persistence.

Provides async database access for retrieving and upserting the calendar
sync cursor (sync_token + page_token) scoped to an Organization and a
specific calendar_id. Each (organization, calendar_id) pair has its own
cursor so that switching the selected calendar does not reuse a stale
sync token from the previous calendar.
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.recruitment.domain.entities import CalendarSyncCursor


class CalendarSyncCursorRepository:
    """Handles CalendarSyncCursor persistence using async SQLAlchemy sessions.

    All cursor operations are scoped by ``calendar_id`` so the sync token
    is tracked per calendar, not per organization. This ensures that
    switching the selected calendar starts a fresh sync rather than
    reusing a stale token from the previous calendar.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: The async database session for executing queries.
        """
        self.session = session

    async def get_cursor(self, calendar_id: str) -> CalendarSyncCursor | None:
        """Retrieve the calendar sync cursor for the given calendar.

        Args:
            calendar_id: The Google Calendar ID to look up.

        Returns:
            The CalendarSyncCursor if found, else None.
        """
        statement = select(CalendarSyncCursor).where(
            CalendarSyncCursor.organization_singleton_key == "default",
            CalendarSyncCursor.calendar_id == calendar_id,
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def upsert_cursor(
        self,
        *,
        calendar_id: str,
        sync_token: str | None = None,
        page_token: str | None = None,
    ) -> CalendarSyncCursor:
        """Create or update the calendar sync cursor for the given calendar.

        The composite unique constraint on (organization_singleton_key, calendar_id)
        ensures one cursor per calendar. When the selected calendar changes,
        a new cursor is created automatically (old cursor remains for
        potential rollback but is no longer queried).

        Args:
            calendar_id: The Google Calendar ID this cursor belongs to.
            sync_token: The next sync token from Google Calendar, or None
                to clear it (on 410 GONE).
            page_token: The next page token for pagination, or None.

        Returns:
            The created or updated CalendarSyncCursor entity.
        """
        now = datetime.now(UTC)

        statement = select(CalendarSyncCursor).where(
            CalendarSyncCursor.organization_singleton_key == "default",
            CalendarSyncCursor.calendar_id == calendar_id,
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
            calendar_id=calendar_id,
            sync_token=sync_token,
            page_token=page_token,
            last_sync_at=now,
        )
        self.session.add(cursor)
        await self.session.flush()
        return cursor

    async def clear_sync_token(self, calendar_id: str) -> None:
        """Clear the sync token for the given calendar after a 410 GONE response.

        The page_token is also cleared. The cursor record itself is kept
        so the next sync starts from a bounded full sync.

        Args:
            calendar_id: The Google Calendar ID whose token to clear.
        """
        cursor = await self.get_cursor(calendar_id)
        if cursor is not None:
            cursor.sync_token = None
            cursor.page_token = None
            cursor.last_sync_at = datetime.now(UTC)
            cursor.updated_at = datetime.now(UTC)
            self.session.add(cursor)
            await self.session.flush()
