"""CalendarSyncService for periodic calendar event synchronization.

Orchestrates event syncing from the selected Google Calendar (via the
Organization Google Connection) and applies changes to Interview and
InterviewParticipant records. Handles incremental sync (sync_token-based),
pagination, 410 GONE recovery (bounded full sync), idempotent updates,
and health status reporting.

Per GH #156:
- RSVP changes are reflected on InterviewParticipant.response_status.
- Event deletion sets Interview.status to "cancelled" without changing
  Candidate pipeline status.
- Time/location/meeting changes update the Interview record.
- Declined/tentative RSVPs create info only, no Interview cancellation.
- Idempotency: duplicate pages/events do not apply changes twice.
- Quota/network failures degrade sync health without losing connection authority.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

import httpx

from src.modules.recruitment.domain.entities import (
    Interview,
    InterviewParticipant,
)
from src.modules.recruitment.domain.value_objects import SyncEventChanges

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.recruitment.infrastructure.calendar_adapter import CalendarAdapter
    from src.modules.recruitment.infrastructure.sync_cursor_repository import (
        CalendarSyncCursorRepository,
    )

logger = logging.getLogger(__name__)

_RSVP_MAP = {
    "needsAction": "needsAction",
    "accepted": "accepted",
    "declined": "declined",
    "tentative": "tentative",
}
_BOUNDED_SYNC_DAYS_PAST = 30
_BOUNDED_SYNC_DAYS_FUTURE = 90


class CalendarSyncService:
    """Orchestrates calendar event synchronisation for recruitment interviews.

    Reads events from the selected Google Calendar via the adapter, matches
    them to Interview records by ``calendar_event_id``, and applies changes:

    - **Event updated** → update Interview ``start_at``, ``end_at``,
      ``timezone``, ``meeting_link``, ``calendar_etag``, ``calendar_updated``.
    - **Event cancelled/deleted** → set Interview status to ``cancelled``
      (no Candidate pipeline change).
    - **Attendee RSVP** → update ``InterviewParticipant.response_status``.
    - **Idempotent** → skip when ``calendar_etag`` matches.

    Args:
        adapter: CalendarAdapter for Google Calendar API calls.
        sync_cursor_repo: Repository for sync cursor (sync_token) persistence.
        calendar_id: The selected calendar ID to sync from.
    """

    def __init__(
        self,
        adapter: CalendarAdapter,
        sync_cursor_repo: CalendarSyncCursorRepository,
        calendar_id: str,
    ) -> None:
        self._adapter = adapter
        self._sync_cursor_repo = sync_cursor_repo
        self._calendar_id = calendar_id

    async def sync_events(
        self,
        access_token: str,
        session: AsyncSession,
        *,
        full_sync: bool = False,
    ) -> int:
        """Execute one sync cycle: fetch changes and apply them to Interviews.

        When ``full_sync`` is True, a bounded full sync (last 30 days) is
        performed regardless of any stored sync token. Otherwise, the stored
        sync token is used for incremental sync. On 410 GONE, the token is
        cleared and a bounded full sync follows.

        Args:
            access_token: Decrypted OAuth access token.
            session: Async database session for Interview queries.
            full_sync: Force a bounded full sync instead of incremental.

        Returns:
            Number of changed events processed (0 if no changes).

        Raises:
            httpx.HTTPStatusError: On 401 (caller should refresh token).
        """
        cursor = await self._sync_cursor_repo.get_cursor(self._calendar_id)
        sync_token = None if full_sync else (cursor.sync_token if cursor else None)

        if sync_token is not None:
            # Incremental sync with stored token.
            try:
                changes = await self._fetch_page(access_token, sync_token=sync_token)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 410:
                    logger.warning(
                        "Calendar sync token expired (410); clearing and falling back to full sync"
                    )
                    await self._sync_cursor_repo.clear_sync_token(self._calendar_id)
                    return await self.sync_events(access_token, session, full_sync=True)
                raise
        else:
            # Bounded full sync (initial or after 410 recovery).
            now = datetime.now(UTC)
            time_min = (now - timedelta(days=_BOUNDED_SYNC_DAYS_PAST)).isoformat()
            time_max = (now + timedelta(days=_BOUNDED_SYNC_DAYS_FUTURE)).isoformat()
            changes = await self._fetch_page(
                access_token,
                time_min=time_min,
                time_max=time_max,
            )

        if not changes.events and changes.next_sync_token is None:
            return 0

        processed = await self._apply_changes(changes, session)

        # Persist the next sync token.
        if changes.next_sync_token:
            await self._sync_cursor_repo.upsert_cursor(
                calendar_id=self._calendar_id,
                sync_token=changes.next_sync_token,
            )

        return processed

    async def _fetch_page(
        self,
        access_token: str,
        *,
        sync_token: str | None = None,
        page_token: str | None = None,
        time_min: str | None = None,
        time_max: str | None = None,
    ) -> SyncEventChanges:
        """Fetch one page of changes, following pagination recursively.

        When the response has a ``next_page_token`` but no ``next_sync_token``,
        the next page is fetched and merged so the caller receives the complete
        set of changes for this sync cycle.

        When ``time_min`` and ``time_max`` are provided (bounded full sync
        without a sync token), they are forwarded to the adapter to limit
        the fetch window to ``_BOUNDED_SYNC_DAYS_PAST`` through
        ``_BOUNDED_SYNC_DAYS_FUTURE``.
        """
        changes = await self._adapter.list_events(
            access_token,
            self._calendar_id,
            sync_token=sync_token,
            page_token=page_token,
            time_min=time_min,
            time_max=time_max,
        )

        # Accumulate paginated results.
        all_events = list(changes.events)
        current_page_token = changes.next_page_token

        while current_page_token is not None and changes.next_sync_token is None:
            page = await self._adapter.list_events(
                access_token,
                self._calendar_id,
                sync_token=sync_token,
                page_token=current_page_token,
                time_min=time_min,
                time_max=time_max,
            )
            all_events.extend(page.events)
            current_page_token = page.next_page_token
            if page.next_sync_token is not None:
                changes = SyncEventChanges(
                    events=tuple(all_events),
                    next_sync_token=page.next_sync_token,
                )
                return changes

        # No next_sync_token yet — still paginating within the initial batch.
        if current_page_token is not None:
            return SyncEventChanges(
                events=tuple(all_events),
                next_page_token=current_page_token,
            )

        return changes

    async def _apply_changes(
        self,
        changes: SyncEventChanges,
        session: AsyncSession,
    ) -> int:
        """Apply sync changes to Interview and InterviewParticipant records.

        Processes each changed CalendarEvent:
        1. Find the matching Interview by ``calendar_event_id``.
        2. Skip if the stored ``calendar_etag`` matches the remote event's
           etag (idempotent — duplicate page/retry guard).
        3. If the event is cancelled/deleted, cancel the Interview.
        4. Otherwise, update time/location/metadata and participant RSVPs.
        5. Declined/tentative participants only update
           ``response_status`` — never cancel the Interview.

        Returns:
            Number of Interviews that were changed.
        """
        count = 0
        from sqlmodel import select

        for cal_event in changes.events:
            # Find matching Interview.
            stmt = select(Interview).where(Interview.calendar_event_id == cal_event.event_id)
            result = await session.execute(stmt)
            interview = result.scalars().first()

            if interview is None:
                # Event not tracked by Vroom — skip.
                continue

            # Idempotency guard: skip if etag matches and update time not newer.
            if cal_event.etag and cal_event.etag == interview.calendar_etag:
                continue
            if (
                cal_event.updated
                and interview.calendar_updated
                and cal_event.updated <= interview.calendar_updated
            ):
                continue
            if cal_event.status == "cancelled":
                if interview.status != "cancelled":
                    interview.status = "cancelled"
            else:
                # Update time/location/metadata.
                interview.calendar_etag = cal_event.etag
                interview.calendar_updated = cal_event.updated

                if cal_event.start_at is not None:
                    interview.start_at = cal_event.start_at
                if cal_event.end_at is not None:
                    interview.end_at = cal_event.end_at
                if cal_event.timezone is not None:
                    interview.timezone = cal_event.timezone

                if cal_event.location is not None:
                    interview.remote_location = cal_event.location

                if cal_event.meet_link is not None:
                    interview.meeting_link = cal_event.meet_link

            # Update participant RSVPs.
            await self._update_participant_rsvps(session, interview.id, cal_event.attendees)

            session.add(interview)
            count += 1

        if count > 0:
            await session.commit()

        return count

    async def _update_participant_rsvps(
        self,
        session: AsyncSession,
        interview_id: UUID,
        attendees: tuple[dict[str, Any], ...],
    ) -> None:
        """Update InterviewParticipant.response_status from attendee data.

        For each attendee in the Calendar event data, find the matching
        InterviewParticipant by email and update their ``response_status``.
        Declined/tentative responses only set the field — they do NOT cancel
        the Interview or trigger any Candidate pipeline change.
        """
        from sqlmodel import select

        for attendee in attendees:
            email = attendee.get("email")
            response_status = attendee.get("responseStatus")
            if not email or not response_status:
                continue

            mapped = _RSVP_MAP.get(response_status)
            if mapped is None:
                continue

            stmt = select(InterviewParticipant).where(
                InterviewParticipant.interview_id == interview_id,
                InterviewParticipant.email == email,
            )
            result = await session.execute(stmt)
            participant = result.scalars().first()

            if participant is not None:
                participant.response_status = mapped
                session.add(participant)

    async def sync_on_token_refresh(
        self,
        access_token: str,
        session: AsyncSession,
    ) -> int:
        """Run a full sync after token refresh/reconnect.

        This clears any stored sync token and runs a bounded full sync so the
        system catches up with any changes that occurred while disconnected.
        """
        await self._sync_cursor_repo.clear_sync_token(self._calendar_id)
        return await self.sync_events(access_token, session, full_sync=True)
