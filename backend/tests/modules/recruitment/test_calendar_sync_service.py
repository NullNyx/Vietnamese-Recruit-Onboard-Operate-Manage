"""Tests for the CalendarSyncService and CalendarAdapter.list_events.

These tests exercise:
1. CalendarAdapter.list_events request construction with syncToken/pagination/410
2. CalendarSyncService._apply_changes for event updates, cancellations, RSVPs
3. CalendarSyncService.sync_events end-to-end with pagination and 410 recovery
4. Idempotency (duplicate pages/retries)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from src.modules.recruitment.application.calendar_sync_service import CalendarSyncService
from src.modules.recruitment.domain.entities import (
    CalendarSyncCursor,
    Interview,
    InterviewParticipant,
)
from src.modules.recruitment.domain.value_objects import (
    CalendarEvent,
    SyncEventChanges,
)
from src.modules.recruitment.infrastructure.calendar_adapter import CalendarAdapter
from src.modules.recruitment.infrastructure.config import RecruitmentSettings

_CAL_BASE = "https://www.googleapis.com/calendar/v3"
_TZ_NAME = "Asia/Ho_Chi_Minh"
_ACCESS_TOKEN = "ya29.sync-test-token"
_CALENDAR_ID = "recruitment@example.com"
_ETAG_1 = '"etag-001"'
_ETAG_2 = '"etag-002"'
_ETAG_3 = '"etag-003"'

Handler = Callable[[httpx.Request], httpx.Response]


# ---------------------------------------------------------------------------
# Adapter tests — list_events request construction
# ---------------------------------------------------------------------------


@dataclass
class _Recorder:
    """Records the requests the adapter sends."""
    by_method: dict[str, dict[str, Any]] = field(default_factory=dict)

    def capture(self, request: httpx.Request) -> None:
        body = None
        if request.content:
            body = json.loads(request.content)
        self.by_method[request.method] = {
            "path": request.url.path,
            "params": dict(request.url.params),
            "body": body,
        }


def _sync_response_json(
    *,
    next_sync_token: str | None = "tok-next",
    next_page_token: str | None = None,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a realistic Google Calendar events.list response."""
    items = events or [
        {
            "id": "evt-001",
            "etag": _ETAG_1,
            "status": "confirmed",
            "htmlLink": "https://calendar.google.com/event?eid=evt-001",
            "start": {"dateTime": "2025-06-01T09:00:00+07:00", "timeZone": _TZ_NAME},
            "end": {"dateTime": "2025-06-01T10:00:00+07:00", "timeZone": _TZ_NAME},
            "attendees": [
                {"email": "candidate@example.com", "responseStatus": "accepted"},
                {"email": "interviewer@example.com", "responseStatus": "needsAction"},
            ],
        }
    ]
    data: dict[str, Any] = {"items": items}
    if next_sync_token:
        data["nextSyncToken"] = next_sync_token
    if next_page_token:
        data["nextPageToken"] = next_page_token
    return data


@pytest.fixture
async def make_adapter() -> AsyncIterator[Callable[[Handler], CalendarAdapter]]:
    clients: list[httpx.AsyncClient] = []

    def _factory(handler: Handler) -> CalendarAdapter:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        clients.append(client)
        settings = RecruitmentSettings(calendar_api_base_url=_CAL_BASE)
        return CalendarAdapter(settings=settings, http_client=client)

    yield _factory
    for client in clients:
        await client.aclose()


class TestListEventsRequestConstruction:
    """Tests for the request the adapter sends on ``list_events``."""

    async def test_list_events_sends_show_deleted_and_single_events(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """list_events sends showDeleted=true and singleEvents=true."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_sync_response_json())

        adapter = make_adapter(handler)
        await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID)

        params = recorder.by_method["GET"]["params"]
        assert params["showDeleted"] == "true"
        assert params["singleEvents"] == "true"

    async def test_list_events_sends_sync_token_when_provided(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """syncToken is included in query params when provided."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_sync_response_json())

        adapter = make_adapter(handler)
        await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID, sync_token="tok-abc")

        assert recorder.by_method["GET"]["params"].get("syncToken") == "tok-abc"

    async def test_list_events_sends_page_token_when_provided(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """pageToken is included in query params when provided."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_sync_response_json())

        adapter = make_adapter(handler)
        await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID, page_token="tok-page-2")

        assert recorder.by_method["GET"]["params"].get("pageToken") == "tok-page-2"

    async def test_list_events_reraises_401(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """list_events re-raises 401 for token refresh handling."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "invalid_credentials"})

        adapter = make_adapter(handler)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID)
        assert exc_info.value.response.status_code == 401

    async def test_list_events_reraises_410(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """list_events re-raises 410 so caller can clear cursor."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(410, json={"error": "sync token expired"})

        adapter = make_adapter(handler)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID, sync_token="tok-expired")
        assert exc_info.value.response.status_code == 410

    async def test_list_events_parses_sync_changes(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """list_events returns a SyncEventChanges with parsed events and tokens."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=_sync_response_json(next_sync_token="tok-new", next_page_token="tok-page"),
            )

        adapter = make_adapter(handler)
        result = await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID)

        assert result.next_sync_token == "tok-new"
        assert result.next_page_token == "tok-page"
        assert len(result.events) == 1
        assert result.events[0].event_id == "evt-001"
        assert result.events[0].etag == _ETAG_1
        assert result.events[0].status == "confirmed"

    async def test_list_events_parses_deleted_event(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """A cancelled/deleted event is parsed with status='cancelled'."""

        def handler(request: httpx.Request) -> httpx.Response:
            items = [{"id": "evt-cancelled", "status": "cancelled", "etag": _ETAG_2}]
            return httpx.Response(200, json=_sync_response_json(events=items))

        adapter = make_adapter(handler)
        result = await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID)

        assert len(result.events) == 1
        assert result.events[0].status == "cancelled"

    async def test_list_events_sends_time_min_max_during_full_sync(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """timeMin/timeMax are included in params when no sync token."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_sync_response_json())

        adapter = make_adapter(handler)
        await adapter.list_events(
            _ACCESS_TOKEN, _CALENDAR_ID,
            time_min="2025-05-01T00:00:00Z",
            time_max="2025-08-01T00:00:00Z",
        )

        params = recorder.by_method["GET"]["params"]
        assert params["timeMin"] == "2025-05-01T00:00:00Z"
        assert params["timeMax"] == "2025-08-01T00:00:00Z"

    async def test_list_events_omits_time_params_during_incremental_sync(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """timeMin/timeMax are NOT included when sync_token is present."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_sync_response_json())

        adapter = make_adapter(handler)
        await adapter.list_events(
            _ACCESS_TOKEN, _CALENDAR_ID,
            sync_token="tok-existing",
            time_min="2025-05-01T00:00:00Z",
            time_max="2025-08-01T00:00:00Z",
        )

        params = recorder.by_method["GET"]["params"]
        assert "timeMin" not in params
        assert "timeMax" not in params

    async def test_list_events_parses_location(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """The location field is parsed from the event response."""

        def handler(request: httpx.Request) -> httpx.Response:
            items = [{
                "id": "evt-loc",
                "status": "confirmed",
                "etag": _ETAG_1,
                "location": "123 Main St, Ho Chi Minh City",
                "start": {"dateTime": "2025-06-01T09:00:00+07:00", "timeZone": _TZ_NAME},
                "end": {"dateTime": "2025-06-01T10:00:00+07:00", "timeZone": _TZ_NAME},
            }]
            return httpx.Response(200, json=_sync_response_json(events=items))

        adapter = make_adapter(handler)
        result = await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID)

        assert len(result.events) == 1
        assert result.events[0].location == "123 Main St, Ho Chi Minh City"

    async def test_list_events_location_is_none_when_absent(
        self, make_adapter: Callable[..., CalendarAdapter]
    ) -> None:
        """Location is None when not present in the event response."""

        def handler(request: httpx.Request) -> httpx.Response:
            items = [{
                "id": "evt-noloc",
                "status": "confirmed",
                "etag": _ETAG_1,
                "start": {"dateTime": "2025-06-01T09:00:00+07:00", "timeZone": _TZ_NAME},
                "end": {"dateTime": "2025-06-01T10:00:00+07:00", "timeZone": _TZ_NAME},
            }]
            return httpx.Response(200, json=_sync_response_json(events=items))

        adapter = make_adapter(handler)
        result = await adapter.list_events(_ACCESS_TOKEN, _CALENDAR_ID)

        assert len(result.events) == 1
        assert result.events[0].location is None


# ---------------------------------------------------------------------------
# Sync service tests — in-memory session with fake cursor repo
# ---------------------------------------------------------------------------


class FakeSyncCursorRepo:
    """In-memory CalendarSyncCursorRepository for testing."""

    def __init__(self) -> None:
        self.cursor = CalendarSyncCursor(
            organization_singleton_key="default",
            sync_token=None,
            page_token=None,
            last_sync_at=None,
        )
        self.upsert_calls: list[dict[str, Any]] = []
        self.clear_calls = 0

    async def get_cursor(self, calendar_id: str) -> CalendarSyncCursor | None:
        return self.cursor

    async def upsert_cursor(
        self, *, calendar_id: str, sync_token: str | None = None, page_token: str | None = None
    ) -> CalendarSyncCursor:
        self.upsert_calls.append({"calendar_id": calendar_id, "sync_token": sync_token, "page_token": page_token})
        if sync_token is not None:
            self.cursor.sync_token = sync_token
        self.cursor.page_token = page_token
        self.cursor.last_sync_at = datetime.now(UTC)
        return self.cursor

    async def clear_sync_token(self, calendar_id: str) -> None:
        self.clear_calls += 1
        self.cursor.sync_token = None
        self.cursor.page_token = None


class FakeInterviewSession:
    """Minimal in-memory session for testing sync service _apply_changes."""

    def __init__(self) -> None:
        self.interviews: dict[str, Interview] = {}
        self.participants: list[InterviewParticipant] = []
        self.added: list[Any] = []
        self.committed = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def execute(self, stmt: Any) -> Any:
        """Simulate select queries for Interview and InterviewParticipant."""
        from sqlalchemy.sql.expression import Select as SA_Select

        if isinstance(stmt, SA_Select):
            compiled = stmt.compile()
            params = compiled.params
            param_values = [str(v) for v in params.values()]

            # Try matching Interview by calendar_event_id
            for iv in self.interviews.values():
                if iv.calendar_event_id and iv.calendar_event_id in param_values:
                    return _FakeResult([iv])

            # Try matching Interview by id for participant query
            for iv in self.interviews.values():
                if str(iv.id) in param_values:
                    # This is likely an interview participant query
                    participants = [
                        p for p in self.participants if str(p.interview_id) in param_values
                        and (len(param_values) <= 1 or p.email in param_values)
                    ]
                    if participants:
                        # Return first matching participant
                        filtered = [
                            p for p in self.participants
                            if str(p.interview_id) in param_values
                        ]
                        # If email filter is present, narrow
                        for val in param_values:
                            if '@' in val:
                                filtered = [p for p in filtered if p.email == val]
                        if filtered:
                            return _FakeResult([filtered[0]])
                    return _FakeResult([])

            return _FakeResult([])
        return _FakeResult([])

    async def commit(self) -> None:
        self.committed = True
        for obj in self.added:
            if isinstance(obj, Interview):
                self.interviews[obj.calendar_event_id or ""] = obj
            elif isinstance(obj, InterviewParticipant):
                self.participants.append(obj)


class _FakeScalars:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def first(self) -> Any:
        return self._items[0] if self._items else None

    def all(self) -> list[Any]:
        return list(self._items)


class _FakeResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def scalars(self) -> _FakeScalars:
        return _FakeScalars(self._items)

    def first(self) -> Any:
        return self._items[0] if self._items else None

    def all(self) -> list[Any]:
        return list(self._items)


def make_interview(
    *,
    calendar_event_id: str = "evt-001",
    etag: str | None = None,
    status: str = "scheduled",
    start_at: datetime | None = None,
) -> Interview:
    """Build an Interview entity for testing."""
    start = start_at or (datetime.now(UTC) + timedelta(days=1))
    return Interview(
        id=uuid4(),
        candidate_id=uuid4(),
        status=status,
        round_name="Technical Round 1",
        start_at=start,
        end_at=start + timedelta(hours=1),
        timezone=_TZ_NAME,
        calendar_event_id=calendar_event_id,
        calendar_etag=etag,
        meeting_mode="google_meet",
    )


@pytest.fixture
def fake_cursor_repo() -> FakeSyncCursorRepo:
    return FakeSyncCursorRepo()


@pytest.fixture
def fake_adapter() -> AsyncMock:
    """Return an AsyncMock CalendarAdapter with manual list_events control."""
    mock = AsyncMock(spec=CalendarAdapter)
    return mock


@pytest.fixture
def sync_service(
    fake_adapter: AsyncMock,
    fake_cursor_repo: FakeSyncCursorRepo,
) -> CalendarSyncService:
    return CalendarSyncService(
        adapter=fake_adapter,
        sync_cursor_repo=fake_cursor_repo,
        calendar_id=_CALENDAR_ID,
    )


# ---------------------------------------------------------------------------
# Sync service: _apply_changes tests
# ---------------------------------------------------------------------------


class TestApplyChanges:

    async def test_apply_skips_unknown_event(self) -> None:
        """An event that doesn't match any Interview is skipped."""
        session = FakeInterviewSession()
        service = CalendarSyncService(
            adapter=AsyncMock(),
            sync_cursor_repo=FakeSyncCursorRepo(),
            calendar_id=_CALENDAR_ID,
        )
        changes = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-unknown",
                    html_link=None,
                    meet_link=None,
                    invited_emails=(),
                ),
            ),
            next_sync_token="tok-next",
        )

        count = await service._apply_changes(changes, session)
        assert count == 0

    async def test_apply_skips_unchanged_etag(self) -> None:
        """An event with matching etag is skipped (idempotent)."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-001", etag=_ETAG_1)
        session.interviews["evt-001"] = iv

        service = CalendarSyncService(
            adapter=AsyncMock(),
            sync_cursor_repo=FakeSyncCursorRepo(),
            calendar_id=_CALENDAR_ID,
        )
        changes = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-001",
                    html_link=None,
                    meet_link=None,
                    invited_emails=(),
                    etag=_ETAG_1,
                ),
            ),
            next_sync_token="tok-next",
        )

        count = await service._apply_changes(changes, session)
        assert count == 0

    async def test_apply_cancels_interview_on_deleted_event(self) -> None:
        """A cancelled event sets Interview status to 'cancelled'."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-001", etag=_ETAG_1)
        session.interviews["evt-001"] = iv

        service = CalendarSyncService(
            adapter=AsyncMock(),
            sync_cursor_repo=FakeSyncCursorRepo(),
            calendar_id=_CALENDAR_ID,
        )
        changes = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-001",
                    html_link=None,
                    meet_link=None,
                    invited_emails=(),
                    etag=_ETAG_2,
                    status="cancelled",
                ),
            ),
            next_sync_token="tok-next",
        )

        count = await service._apply_changes(changes, session)
        assert count == 1
        assert iv.status == "cancelled"

    async def test_apply_updates_interview_time(self) -> None:
        """An updated event changes Interview time/location metadata."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-001", etag=_ETAG_1)
        session.interviews["evt-001"] = iv

        service = CalendarSyncService(
            adapter=AsyncMock(),
            sync_cursor_repo=FakeSyncCursorRepo(),
            calendar_id=_CALENDAR_ID,
        )
        changes = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-001",
                    html_link=None,
                    meet_link="https://meet.google.com/new-link",
                    invited_emails=("candidate@example.com",),
                    etag=_ETAG_2,
                    status="confirmed",
                    attendees=(
                        {"email": "candidate@example.com", "responseStatus": "accepted"},
                        {"email": "interviewer@example.com", "responseStatus": "needsAction"},
                    ),
                ),
            ),
            next_sync_token="tok-next",
        )

        count = await service._apply_changes(changes, session)
        assert count == 1
        assert iv.calendar_etag == _ETAG_2
        assert iv.meeting_link == "https://meet.google.com/new-link"

    async def test_apply_does_not_cancel_for_declined_rsvp(self) -> None:
        """A declined attendee updates response_status but does NOT cancel Interview."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-001", etag=_ETAG_1)
        session.interviews["evt-001"] = iv

        participant = InterviewParticipant(
            id=uuid4(),
            interview_id=iv.id,
            type="candidate",
            email="candidate@example.com",
            response_status="needsAction",
        )
        session.participants.append(participant)

        service = CalendarSyncService(
            adapter=AsyncMock(),
            sync_cursor_repo=FakeSyncCursorRepo(),
            calendar_id=_CALENDAR_ID,
        )
        changes = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-001",
                    html_link=None,
                    meet_link=None,
                    invited_emails=(),
                    etag=_ETAG_2,
                    status="confirmed",
                    attendees=(
                        {"email": "candidate@example.com", "responseStatus": "declined"},
                    ),
                ),
            ),
            next_sync_token="tok-next",
        )

        count = await service._apply_changes(changes, session)
        assert count == 1
        assert iv.status == "scheduled"  # Still scheduled — not cancelled

    async def test_apply_updates_participant_rsvp(
        self, sync_service: CalendarSyncService
    ) -> None:
        """RSVP changes are propagated to InterviewParticipant.response_status."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-001", etag=_ETAG_1)
        session.interviews["evt-001"] = iv

        participant = InterviewParticipant(
            id=uuid4(),
            interview_id=iv.id,
            type="employee",
            email="interviewer@example.com",
            response_status="needsAction",
        )
        session.participants.append(participant)

        await sync_service._update_participant_rsvps(
            session,
            iv.id,
            (
                {"email": "interviewer@example.com", "responseStatus": "accepted"},
            ),
        )

        # Check the participant was updated
        assert len(session.added) > 0
        added_participants = [p for p in session.added if isinstance(p, InterviewParticipant)]
        assert len(added_participants) >= 1
        updated = added_participants[-1]
        assert updated.response_status == "accepted"


# ---------------------------------------------------------------------------
# Sync service: sync_events end-to-end
# ---------------------------------------------------------------------------


class TestSyncEvents:

    async def test_sync_without_cursor_does_full_sync(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """No cursor → list_events called without syncToken."""
        fake_cursor_repo.cursor.sync_token = None
        fake_adapter.list_events.return_value = SyncEventChanges(
            events=(),
            next_sync_token="tok-initial",
        )

        session = FakeInterviewSession()
        count = await sync_service.sync_events(_ACCESS_TOKEN, session)

        fake_adapter.list_events.assert_called_once()
        call_kwargs = fake_adapter.list_events.call_args[1]
        assert call_kwargs.get("sync_token") is None
        assert count == 0

        # Check token was persisted
        assert fake_cursor_repo.cursor.sync_token == "tok-initial"

    async def test_sync_with_cursor_does_incremental(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """Existing cursor → list_events called with syncToken."""
        fake_cursor_repo.cursor.sync_token = "tok-existing"
        fake_adapter.list_events.return_value = SyncEventChanges(
            events=(),
            next_sync_token="tok-new",
        )

        session = FakeInterviewSession()
        await sync_service.sync_events(_ACCESS_TOKEN, session)

        fake_adapter.list_events.assert_called_once()
        call_kwargs = fake_adapter.list_events.call_args[1]
        assert call_kwargs.get("sync_token") == "tok-existing"

    async def test_sync_410_clears_cursor_and_retries(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """410 GONE clears the cursor and falls back to bounded full sync."""
        fake_cursor_repo.cursor.sync_token = "tok-expired"

        # First call raises 410, second succeeds.
        request = httpx.Request("GET", "https://calendar/v3/calendars/x/events")
        response = httpx.Response(410, request=request)
        fake_adapter.list_events.side_effect = [
            httpx.HTTPStatusError("410 Gone", request=request, response=response),
            SyncEventChanges(events=(), next_sync_token="tok-fresh"),
        ]

        session = FakeInterviewSession()
        await sync_service.sync_events(_ACCESS_TOKEN, session)

        # Cursor was cleared and full sync ran
        assert fake_cursor_repo.clear_calls == 1
        assert fake_adapter.list_events.call_count == 2

        # The retry call had no sync token (full sync)
        retry_kwargs = fake_adapter.list_events.call_args[1]
        assert retry_kwargs.get("sync_token") is None

    async def test_sync_applies_event_changes(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """Events returned from list_events are applied to Interviews."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-sync", etag="old-etag")
        session.interviews["evt-sync"] = iv

        fake_cursor_repo.cursor.sync_token = "tok-existing"
        fake_adapter.list_events.return_value = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-sync",
                    html_link=None,
                    meet_link="https://meet.google.com/synced",
                    invited_emails=(),
                    etag="new-etag",
                    status="confirmed",
                ),
            ),
            next_sync_token="tok-new",
        )

        count = await sync_service.sync_events(_ACCESS_TOKEN, session)

        assert count == 1
        assert iv.calendar_etag == "new-etag"
        assert iv.meeting_link == "https://meet.google.com/synced"
        assert fake_cursor_repo.cursor.sync_token == "tok-new"

    async def test_sync_deleted_event_cancels_interview(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """A cancelled/deleted event transitions Interview to cancelled."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-dell", etag="old-etag")
        session.interviews["evt-dell"] = iv

        fake_adapter.list_events.return_value = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-dell",
                    html_link=None,
                    meet_link=None,
                    invited_emails=(),
                    etag="new-etag",
                    status="cancelled",
                ),
            ),
            next_sync_token="tok-new",
        )

        await sync_service.sync_events(_ACCESS_TOKEN, session)
        assert iv.status == "cancelled"

    async def test_full_sync_sends_time_bounds(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """Full sync (no cursor) sends timeMin/timeMax params to adapter."""
        fake_cursor_repo.cursor.sync_token = None
        fake_adapter.list_events.return_value = SyncEventChanges(
            events=(),
            next_sync_token="tok-after-full",
        )

        session = FakeInterviewSession()
        await sync_service.sync_events(_ACCESS_TOKEN, session)

        fake_adapter.list_events.assert_called_once()
        call_kwargs = fake_adapter.list_events.call_args[1]
        # time_min and time_max should be set for full sync
        assert call_kwargs.get("time_min") is not None
        assert call_kwargs.get("time_max") is not None
        assert call_kwargs.get("sync_token") is None

    async def test_incremental_sync_omits_time_bounds(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """Incremental sync (with cursor) does NOT send timeMin/timeMax."""
        fake_cursor_repo.cursor.sync_token = "tok-existing"
        fake_adapter.list_events.return_value = SyncEventChanges(
            events=(),
            next_sync_token="tok-new",
        )

        session = FakeInterviewSession()
        await sync_service.sync_events(_ACCESS_TOKEN, session)

        fake_adapter.list_events.assert_called_once()
        call_kwargs = fake_adapter.list_events.call_args[1]
        assert call_kwargs.get("sync_token") == "tok-existing"
        # time_min and time_max should NOT be set for incremental sync
        assert call_kwargs.get("time_min") is None
        assert call_kwargs.get("time_max") is None

    async def test_apply_remote_location_from_synced_event(
        self,
        fake_adapter: AsyncMock,
        fake_cursor_repo: FakeSyncCursorRepo,
        sync_service: CalendarSyncService,
    ) -> None:
        """An event with location updates Interview.remote_location."""
        session = FakeInterviewSession()
        iv = make_interview(calendar_event_id="evt-loc-sync", etag="old-etag")
        session.interviews["evt-loc-sync"] = iv

        fake_adapter.list_events.return_value = SyncEventChanges(
            events=(
                CalendarEvent(
                    event_id="evt-loc-sync",
                    html_link=None,
                    meet_link=None,
                    location="123 Main St, Ho Chi Minh City",
                    invited_emails=(),
                    etag="new-etag",
                    status="confirmed",
                ),
            ),
            next_sync_token="tok-new",
        )

        await sync_service.sync_events(_ACCESS_TOKEN, session)
        assert iv.calendar_etag == "new-etag"
        assert iv.remote_location == "123 Main St, Ho Chi Minh City"

