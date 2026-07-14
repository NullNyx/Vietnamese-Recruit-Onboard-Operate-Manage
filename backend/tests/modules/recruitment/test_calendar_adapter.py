"""Unit tests for CalendarAdapter request construction.

Exercises the HTTP requests the adapter sends to the Google Calendar API using
``httpx.MockTransport`` so no real network calls are made. The handler inspects
``request.url.params``, ``request.url.path``, and ``json.loads(request.content)``
and returns scripted ``httpx.Response`` objects. Covers, per ADR-0008:

- ``conferenceDataVersion=1`` and ``conferenceData.createRequest`` present on
  create and absent on patch (so the Meet link is preserved) (R6.1, R7.2).
- ``sendUpdates=all`` present on create, patch, and delete.
- ``start``/``end`` serialized as RFC3339 ``{dateTime, timeZone}`` objects.
- ``401`` re-raised (not swallowed) so the service can refresh the token.
- ``delete_event`` treats ``404``/``410`` as success (R8.1).

Requirements: 6.1, 7.2, 8.1
"""

import json
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest

from src.modules.recruitment.domain.exceptions import (
    CalendarEventCreateFailedError,
    CalendarEventUpdateFailedError,
)
from src.modules.recruitment.domain.value_objects import CalendarEventSpec
from src.modules.recruitment.infrastructure.calendar_adapter import CalendarAdapter
from src.modules.recruitment.infrastructure.config import RecruitmentSettings

_CAL_BASE = "https://www.googleapis.com/calendar/v3"
_TZ_NAME = "Asia/Ho_Chi_Minh"
_TZ = ZoneInfo(_TZ_NAME)
_ACCESS_TOKEN = "ya29.access-token"  # noqa: S105 - test fixture value, not a real secret
_EVENT_ID = "evt_abc123"
_MEET_LINK = "https://meet.google.com/abc-defg-hij"

Handler = Callable[[httpx.Request], httpx.Response]
AdapterFactory = Callable[[Handler], CalendarAdapter]


@dataclass
class _Captured:
    """A single request captured by the MockTransport handler."""

    method: str
    path: str
    params: dict[str, str]
    body: dict[str, Any] | None


@dataclass
class _Recorder:
    """Records the requests the adapter sends, keyed by HTTP method."""

    by_method: dict[str, _Captured] = field(default_factory=dict)

    def capture(self, request: httpx.Request) -> None:
        """Store a captured view of the given request keyed by its method."""
        body: dict[str, Any] | None = None
        if request.content:
            body = json.loads(request.content)
        self.by_method[request.method] = _Captured(
            method=request.method,
            path=request.url.path,
            params=dict(request.url.params),
            body=body,
        )


def _make_spec(duration_minutes: int = 60, *, request_meet_link: bool = True) -> CalendarEventSpec:
    """Build a timezone-resolved CalendarEventSpec for adapter calls."""
    start = datetime(2025, 6, 1, 9, 0, tzinfo=_TZ)
    end = start + timedelta(minutes=duration_minutes)
    return CalendarEventSpec(
        summary="Interview with Candidate",
        description="Discuss the role and answer questions.",
        start=start,
        end=end,
        timezone=_TZ_NAME,
        attendee_emails=("candidate@example.com", "interviewer@example.com"),
        calendar_id="recruitment@company.vn",
        request_meet_link=request_meet_link,
    )


def _event_response_json(*, event_id: str = _EVENT_ID, with_meet: bool = True) -> dict[str, Any]:
    """Build a realistic Google Calendar event JSON body for create/patch."""
    data: dict[str, Any] = {
        "id": event_id,
        "htmlLink": f"https://www.google.com/calendar/event?eid={event_id}",
        "start": {"dateTime": "2025-06-01T09:00:00+07:00", "timeZone": _TZ_NAME},
        "end": {"dateTime": "2025-06-01T10:00:00+07:00", "timeZone": _TZ_NAME},
        "attendees": [
            {"email": "candidate@example.com"},
            {"email": "interviewer@example.com"},
        ],
    }
    if with_meet:
        data["hangoutLink"] = _MEET_LINK
        data["conferenceData"] = {
            "entryPoints": [{"entryPointType": "video", "uri": _MEET_LINK}],
        }
    return data


@pytest.fixture
async def make_adapter() -> AsyncIterator[AdapterFactory]:
    """Yield a factory building CalendarAdapters wired to a MockTransport handler.

    The factory builds an ``httpx.AsyncClient`` with
    ``transport=httpx.MockTransport(handler)`` so all requests are intercepted.
    Created clients are closed on teardown.
    """
    clients: list[httpx.AsyncClient] = []

    def _factory(handler: Handler) -> CalendarAdapter:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        clients.append(client)
        settings = RecruitmentSettings(calendar_api_base_url=_CAL_BASE)
        return CalendarAdapter(settings=settings, http_client=client)

    yield _factory

    for client in clients:
        await client.aclose()


class TestCreateEventRequestConstruction:
    """Tests for the request the adapter sends on ``create_event``."""

    async def test_create_sends_conference_data_version_and_create_request(
        self, make_adapter: AdapterFactory
    ) -> None:
        """Create sends conferenceDataVersion=1 and conferenceData.createRequest."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        await adapter.create_event(_ACCESS_TOKEN, _make_spec())

        captured = recorder.by_method["POST"]
        assert captured.path == "/calendar/v3/calendars/recruitment@company.vn/events"
        assert captured.params["conferenceDataVersion"] == "1"
        assert captured.body is not None
        conference_data = captured.body["conferenceData"]
        assert "createRequest" in conference_data
        create_request = conference_data["createRequest"]
        assert create_request["conferenceSolutionKey"]["type"] == "hangoutsMeet"
        assert create_request["requestId"]  # a unique, non-empty request id

    async def test_create_includes_send_updates_all(self, make_adapter: AdapterFactory) -> None:
        """Create requests invitation emails via sendUpdates=all."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        await adapter.create_event(_ACCESS_TOKEN, _make_spec())

        assert recorder.by_method["POST"].params["sendUpdates"] == "all"

    async def test_create_serializes_start_and_end_as_rfc3339_objects(
        self, make_adapter: AdapterFactory
    ) -> None:
        """start/end are {dateTime: RFC3339, timeZone: IANA} objects."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        spec = _make_spec(duration_minutes=60)
        await adapter.create_event(_ACCESS_TOKEN, spec)

        body = recorder.by_method["POST"].body
        assert body is not None
        assert body["start"] == {
            "dateTime": "2025-06-01T09:00:00+07:00",
            "timeZone": _TZ_NAME,
        }
        assert body["end"] == {
            "dateTime": "2025-06-01T10:00:00+07:00",
            "timeZone": _TZ_NAME,
        }
        # The serialized dateTime matches the spec exactly (RFC3339 with offset).
        assert body["start"]["dateTime"] == spec.start.isoformat()
        assert body["end"]["dateTime"] == spec.end.isoformat()

    async def test_create_returns_parsed_event_with_meet_link(
        self, make_adapter: AdapterFactory
    ) -> None:
        """A 2xx create response is parsed into a CalendarEvent with the Meet link."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        event = await adapter.create_event(_ACCESS_TOKEN, _make_spec())

        assert event.event_id == _EVENT_ID
        assert event.meet_link == _MEET_LINK
        assert set(event.invited_emails) == {
            "candidate@example.com",
            "interviewer@example.com",
        }


class TestPatchEventRequestConstruction:
    """Tests for the request the adapter sends on ``patch_event``."""

    async def test_patch_omits_conference_data(self, make_adapter: AdapterFactory) -> None:
        """Patch body omits conferenceData so the existing Meet link is preserved."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        await adapter.patch_event(_ACCESS_TOKEN, _EVENT_ID, _make_spec())

        captured = recorder.by_method["PATCH"]
        assert captured.path == f"/calendar/v3/calendars/recruitment@company.vn/events/{_EVENT_ID}"
        assert captured.body is not None
        assert "conferenceData" not in captured.body

    async def test_patch_includes_version_and_send_updates(
        self, make_adapter: AdapterFactory
    ) -> None:
        """Patch still sends conferenceDataVersion=1 and sendUpdates=all."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        await adapter.patch_event(_ACCESS_TOKEN, _EVENT_ID, _make_spec())

        params = recorder.by_method["PATCH"].params
        assert params["conferenceDataVersion"] == "1"
        assert params["sendUpdates"] == "all"

    async def test_patch_serializes_start_and_end_as_rfc3339_objects(
        self, make_adapter: AdapterFactory
    ) -> None:
        """Patch start/end are {dateTime, timeZone} objects."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        spec = _make_spec(duration_minutes=90)
        await adapter.patch_event(_ACCESS_TOKEN, _EVENT_ID, spec)

        body = recorder.by_method["PATCH"].body
        assert body is not None
        assert body["start"] == {"dateTime": spec.start.isoformat(), "timeZone": _TZ_NAME}
        assert body["end"] == {"dateTime": spec.end.isoformat(), "timeZone": _TZ_NAME}


class TestSendUpdatesOnAllOperations:
    """Tests that ``sendUpdates=all`` is present on create, patch, and delete."""

    async def test_send_updates_all_on_create_patch_and_delete(
        self, make_adapter: AdapterFactory
    ) -> None:
        """All three operations include the sendUpdates=all query param."""
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.capture(request)
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(200, json=_event_response_json())

        adapter = make_adapter(handler)
        spec = _make_spec()
        await adapter.create_event(_ACCESS_TOKEN, spec)
        await adapter.patch_event(_ACCESS_TOKEN, _EVENT_ID, spec)
        await adapter.delete_event(_ACCESS_TOKEN, _EVENT_ID, calendar_id="cal-001")

        assert recorder.by_method["POST"].params["sendUpdates"] == "all"
        assert recorder.by_method["PATCH"].params["sendUpdates"] == "all"
        assert recorder.by_method["DELETE"].params["sendUpdates"] == "all"


class TestUnauthorizedReRaise:
    """Tests that a 401 is re-raised (not swallowed) for token refresh."""

    async def test_create_reraises_401(self, make_adapter: AdapterFactory) -> None:
        """create_event re-raises HTTPStatusError on 401, not a create-failed error."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "invalid_credentials"})

        adapter = make_adapter(handler)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await adapter.create_event(_ACCESS_TOKEN, _make_spec())
        assert exc_info.value.response.status_code == 401

    async def test_create_401_is_not_wrapped_as_create_failed(
        self, make_adapter: AdapterFactory
    ) -> None:
        """A 401 must not be swallowed into CalendarEventCreateFailedError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        adapter = make_adapter(handler)
        with pytest.raises(httpx.HTTPStatusError):
            await adapter.create_event(_ACCESS_TOKEN, _make_spec())

    async def test_patch_reraises_401(self, make_adapter: AdapterFactory) -> None:
        """patch_event re-raises HTTPStatusError on 401, not an update-failed error."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        adapter = make_adapter(handler)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await adapter.patch_event(_ACCESS_TOKEN, _EVENT_ID, _make_spec())
        assert exc_info.value.response.status_code == 401

    async def test_delete_reraises_401(self, make_adapter: AdapterFactory) -> None:
        """delete_event re-raises HTTPStatusError on 401 (not treated as gone)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        adapter = make_adapter(handler)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await adapter.delete_event(_ACCESS_TOKEN, _EVENT_ID, calendar_id="recruitment@company.vn")
        assert exc_info.value.response.status_code == 401


class TestNonAuthFailuresWrapped:
    """Tests that non-401 create/patch failures surface as domain errors."""

    async def test_create_4xx_raises_create_failed(self, make_adapter: AdapterFactory) -> None:
        """A non-401 4xx on create raises CalendarEventCreateFailedError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, text="Bad Request")

        adapter = make_adapter(handler)
        with pytest.raises(CalendarEventCreateFailedError):
            await adapter.create_event(_ACCESS_TOKEN, _make_spec())

    async def test_patch_4xx_raises_update_failed(self, make_adapter: AdapterFactory) -> None:
        """A non-401 4xx on patch raises CalendarEventUpdateFailedError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, text="Bad Request")

        adapter = make_adapter(handler)
        with pytest.raises(CalendarEventUpdateFailedError):
            await adapter.patch_event(_ACCESS_TOKEN, _EVENT_ID, _make_spec())


class TestDeleteIdempotency:
    """Tests that ``delete_event`` treats 404/410 as success."""

    async def test_delete_treats_404_as_success(self, make_adapter: AdapterFactory) -> None:
        """A 404 (event already gone) is treated as a successful cancellation."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="Not Found")

        adapter = make_adapter(handler)
        # Should not raise: an already-gone event is an idempotent success.
        await adapter.delete_event(_ACCESS_TOKEN, _EVENT_ID, calendar_id="recruitment@company.vn")

    async def test_delete_treats_410_as_success(self, make_adapter: AdapterFactory) -> None:
        """A 410 (event already deleted) is treated as a successful cancellation."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(410, text="Gone")

        adapter = make_adapter(handler)
        # Should not raise.
        await adapter.delete_event(_ACCESS_TOKEN, _EVENT_ID, calendar_id="recruitment@company.vn")

    async def test_delete_2xx_succeeds(self, make_adapter: AdapterFactory) -> None:
        """A normal 204 delete succeeds without raising."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        adapter = make_adapter(handler)
        # Should not raise.
        await adapter.delete_event(_ACCESS_TOKEN, _EVENT_ID, calendar_id="recruitment@company.vn")
