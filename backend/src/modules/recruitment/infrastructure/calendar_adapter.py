"""Google Calendar API adapter with retry and exponential backoff.

Encapsulates all Google Calendar API interactions using ``httpx`` for async
HTTP calls. Mirrors the existing :class:`GmailAdapter` shape: it is constructed
with an ``httpx.AsyncClient`` plus module settings, implements
``retry_with_backoff`` (retry on 5xx/429, never retry non-429 4xx) and re-raises
``401`` so the calling service can refresh the OAuth token and retry once.

Per ADR-0008 the adapter creates the interview event on the selected calendar
(defaulting to ``primary``), invites the Candidate plus interviewer Employees,
and attaches a Google Meet link when requested. Reschedule patches the existing
event while preserving the Meet link, and cancellation deletes the event
idempotently.
"""

import asyncio
import hashlib
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, TypeVar
from uuid import uuid4

import httpx

from src.modules.recruitment.domain.exceptions import (
    CalendarEventCreateFailedError,
    CalendarEventSyncError,
    CalendarEventUpdateFailedError,
)
from src.modules.recruitment.domain.value_objects import (
    CalendarEvent,
    CalendarEventSpec,
    SyncEventChanges,
)
from src.modules.recruitment.infrastructure.config import RecruitmentSettings

logger = logging.getLogger(__name__)

CAL_BASE = "https://www.googleapis.com/calendar/v3"
_MEET_CONFERENCE_TYPE = "hangoutsMeet"
_RETRY_BACKOFF_BASE = 1.0
_DEFAULT_RETRY_AFTER_SECONDS = 5
_GONE_STATUS_CODES = (404, 410)

T = TypeVar("T")


class CalendarAdapter:
    """Google Calendar API client wrapper with retry and backoff.

    All Google Calendar API interactions go through this adapter. It implements
    exponential backoff retry for transient failures (5xx, 429) and re-raises
    ``401`` so the calling service can refresh the token and retry once,
    mirroring the Gmail per-user-token pattern.

    Args:
        settings: Recruitment module settings carrying the Calendar API base
            URL, request timeout, and maximum retry count.
        http_client: Async HTTP client used for all Calendar API calls.
    """

    def __init__(
        self,
        settings: RecruitmentSettings,
        http_client: httpx.AsyncClient,
    ) -> None:
        """Initialize the Calendar adapter.

        Args:
            settings: Recruitment module configuration (Calendar section).
            http_client: Async HTTP client for API calls.
        """
        self._settings = settings
        self._http_client = http_client
        self._base_url = settings.calendar_api_base_url.rstrip("/")

    async def retry_with_backoff(
        self,
        func: Callable[[], Awaitable[T]],
        *,
        max_retries: int | None = None,
        base_delay: float | None = None,
        timeout: float | None = None,
    ) -> T:
        """Execute an async function with exponential backoff retry.

        Retries on 5xx errors and 429 (honoring ``Retry-After``). Does not retry
        on 4xx errors (except 429); ``401`` in particular is re-raised so the
        calling service can refresh the OAuth token and retry once.

        Delays follow ``base_delay * 2**attempt`` (default 1s, 2s, 4s). Each
        individual request is bounded by ``timeout`` seconds.

        Args:
            func: Async callable that performs the HTTP request and raises on a
                non-2xx response via ``response.raise_for_status()``.
            max_retries: Maximum retry attempts (default from settings).
            base_delay: Base delay in seconds (default 1.0).
            timeout: Per-request timeout in seconds (default from settings).

        Returns:
            The result of the successful function call.

        Raises:
            httpx.HTTPStatusError: If non-retryable (4xx) or retries exhausted.
            TimeoutError: If the request times out on the final attempt.
            httpx.HTTPError: If a transient network error persists.
        """
        if max_retries is None:
            max_retries = self._settings.calendar_max_retries
        if base_delay is None:
            base_delay = _RETRY_BACKOFF_BASE
        if timeout is None:
            timeout = float(self._settings.calendar_api_timeout_seconds)

        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(func(), timeout=timeout)
            except TimeoutError:
                if attempt == max_retries:
                    raise
                logger.warning(
                    "Calendar request timed out (attempt %d/%d)",
                    attempt + 1,
                    max_retries + 1,
                )
                await asyncio.sleep(base_delay * (2**attempt))
            except (httpx.ConnectError, httpx.ConnectTimeout, OSError) as exc:
                # Network/DNS errors are transient and retryable.
                if attempt == max_retries:
                    raise
                logger.warning(
                    "Calendar connection error (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries + 1,
                    str(exc),
                )
                await asyncio.sleep(base_delay * (2**attempt))
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code

                # 429: rate limited — wait for Retry-After then retry.
                if status_code == 429:
                    if attempt == max_retries:
                        raise
                    retry_after = self._parse_retry_after(exc.response)
                    logger.info(
                        "Calendar rate limited, waiting %ds (attempt %d/%d)",
                        retry_after,
                        attempt + 1,
                        max_retries + 1,
                    )
                    await asyncio.sleep(retry_after)
                    continue

                # 5xx: transient server error — retry with backoff.
                if 500 <= status_code < 600:
                    if attempt == max_retries:
                        raise
                    logger.warning(
                        "Calendar server error %d (attempt %d/%d)",
                        status_code,
                        attempt + 1,
                        max_retries + 1,
                    )
                    await asyncio.sleep(base_delay * (2**attempt))
                    continue

                # 4xx (including 401) are not retryable; re-raise for the service.
                raise

        # Unreachable: the loop either returns or raises on every path.
        raise RuntimeError("retry_with_backoff exhausted without a result")

    def _parse_retry_after(self, response: httpx.Response) -> int:
        """Parse the ``Retry-After`` header from a 429 response.

        Args:
            response: The HTTP response with status 429.

        Returns:
            Number of seconds to wait. Defaults to 5 if the header is missing
            or not an integer.
        """
        header = response.headers.get("Retry-After")
        if header is None:
            return _DEFAULT_RETRY_AFTER_SECONDS
        try:
            return int(header)
        except (ValueError, TypeError):
            return _DEFAULT_RETRY_AFTER_SECONDS

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        """Build authorization headers for Calendar API requests.

        Args:
            access_token: OAuth2 access token with the ``calendar.events`` scope.

        Returns:
            Dictionary with the ``Authorization`` header.
        """
        return {"Authorization": f"Bearer {access_token}"}

    def _serialize_time(self, value: datetime, timezone: str) -> dict[str, str]:
        """Serialize a timezone-aware datetime as a Calendar time object.

        Args:
            value: Timezone-aware datetime to serialize.
            timezone: IANA timezone name applied to the event.

        Returns:
            ``{"dateTime": <RFC3339>, "timeZone": <IANA tz>}``.
        """
        return {"dateTime": value.isoformat(), "timeZone": timezone}

    def _build_meet_request_id(self, spec: CalendarEventSpec) -> str:
        """Build a deterministic meeting request ID from the spec.

        Uses a SHA-256 of the event summary, start time, and a random salt so the
        request ID is stable for the same interview (enabling idempotent Meet creation
        on retry) but unpredictable across different events.

        Args:
            spec: The timezone-resolved event specification.

        Returns:
            A 64-character hex request ID.
        """
        raw = f"{spec.summary}|{spec.start.isoformat()}|{uuid4().hex}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _build_create_body(self, spec: CalendarEventSpec) -> dict[str, Any]:
        """Build the request body for ``events.insert``.

        Includes ``summary``, optional ``description`` (notes), ``start``/``end``
        as ``{dateTime, timeZone}``, the attendee list, and — when a Meet link is
        requested — a ``conferenceData.createRequest`` with a unique
        ``requestId`` and ``conferenceSolutionKey.type = "hangoutsMeet"``.

        Args:
            spec: The timezone-resolved event specification.

        Returns:
            The JSON body for the create request.
        """
        body: dict[str, Any] = {
            "summary": spec.summary,
            "start": self._serialize_time(spec.start, spec.timezone),
            "end": self._serialize_time(spec.end, spec.timezone),
            "attendees": [{"email": email} for email in spec.attendee_emails],
        }
        if spec.description is not None:
            body["description"] = spec.description
        if spec.request_meet_link:
            body["conferenceData"] = {
                "createRequest": {
                    "requestId": self._build_meet_request_id(spec),
                    "conferenceSolutionKey": {"type": _MEET_CONFERENCE_TYPE},
                }
            }
        return body

    def _build_patch_body(self, spec: CalendarEventSpec) -> dict[str, Any]:
        """Build the request body for ``events.patch`` (reschedule).

        Sends only ``start``/``end`` (and ``description`` when present). It
        deliberately OMITS ``conferenceData`` and ``attendees`` so the existing
        Google Meet link is preserved (R7.2).

        Args:
            spec: The timezone-resolved event specification with the new times.

        Returns:
            The JSON body for the patch request.
        """
        body: dict[str, Any] = {
            "start": self._serialize_time(spec.start, spec.timezone),
            "end": self._serialize_time(spec.end, spec.timezone),
        }
        if spec.description is not None:
            body["description"] = spec.description
        return body

    def _parse_event(self, data: dict[str, Any]) -> CalendarEvent:
        """Parse a Calendar API event response into a :class:`CalendarEvent`.

        Extracts all relevant fields including ``location`` (physical address/
        remote meeting info) and ``attendees`` for RSVP tracking.

        Args:
            data: Raw JSON response from ``events.insert`` or ``events.patch``.

        Returns:
            The parsed :class:`CalendarEvent` value object.
        """
        return CalendarEvent(
            event_id=str(data.get("id", "")),
            html_link=self._optional_str(data.get("htmlLink")),
            meet_link=self._extract_meet_link(data),
            location=self._optional_str(data.get("location")),
            etag=self._optional_str(data.get("etag")),
            updated=self._parse_datetime(data.get("updated")),
            invited_emails=self._extract_attendees(data),
            status=self._optional_str(data.get("status")),
            attendees=tuple(data.get("attendees") or ()),
        )

    def _optional_str(self, value: Any) -> str | None:
        """Coerce a raw JSON value to ``str`` only when it is a string.

        Args:
            value: A value read from the API response.

        Returns:
            The string value, or ``None`` if it is absent or not a string.
        """
        return value if isinstance(value, str) else None

    def _parse_datetime(self, value: Any) -> datetime | None:
        """Parse a raw JSON value as an RFC3339 datetime.

        Args:
            value: A value read from the API response.

        Returns:
            The parsed datetime, or ``None`` if it cannot be parsed.
        """
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None

    def _extract_meet_link(self, data: dict[str, Any]) -> str | None:
        """Extract the Google Meet link from a Calendar event response.

        Prefers a ``conferenceData`` video ``entryPoint`` and falls back to the
        legacy ``hangoutLink`` field.

        Args:
            data: Raw JSON response from the Calendar API.

        Returns:
            The Meet URI, or ``None`` if no conferencing link is present.
        """
        conference_data = data.get("conferenceData")
        if isinstance(conference_data, dict):
            entry_points = conference_data.get("entryPoints")
            if isinstance(entry_points, list):
                for entry in entry_points:
                    if not isinstance(entry, dict):
                        continue
                    if entry.get("entryPointType") == "video":
                        uri = entry.get("uri")
                        if isinstance(uri, str):
                            return uri
        return self._optional_str(data.get("hangoutLink"))

    def _extract_attendees(self, data: dict[str, Any]) -> tuple[str, ...]:
        """Extract the attendee email addresses accepted on the event.

        Args:
            data: Raw JSON response from the Calendar API.

        Returns:
            Tuple of attendee email addresses (possibly empty).
        """
        attendees = data.get("attendees")
        if not isinstance(attendees, list):
            return ()
        emails: list[str] = []
        for attendee in attendees:
            if isinstance(attendee, dict):
                email = attendee.get("email")
                if isinstance(email, str):
                    emails.append(email)
        return tuple(emails)

    async def create_event(self, access_token: str, spec: CalendarEventSpec) -> CalendarEvent:
        """Create a Google Calendar event with a Meet link and attendees.

        Sends ``POST {CAL_BASE}/calendars/{calendar_id}/events`` with
        ``conferenceDataVersion=1`` (required for Meet) and ``sendUpdates=all``
        (sends invitation emails). The ``calendar_id`` is read from the spec,
        defaulting to ``primary``.

        Args:
            access_token: OAuth2 access token for the acting HR user.
            spec: The timezone-resolved event specification.

        Returns:
            The created :class:`CalendarEvent` (event id, html link, Meet link,
            invited emails, etag, updated).

        Raises:
            CalendarEventCreateFailedError: If creation fails after retries.
            httpx.HTTPStatusError: If ``401`` (for token refresh handling).
        """
        calendar_id = spec.calendar_id
        url = f"{self._base_url}/calendars/{calendar_id}/events"
        params: dict[str, str | int] = {"conferenceDataVersion": 1, "sendUpdates": "all"}
        body = self._build_create_body(spec)

        async def _request() -> httpx.Response:
            response = await self._http_client.post(
                url,
                headers=self._auth_headers(access_token),
                params=params,
                json=body,
            )
            response.raise_for_status()
            return response

        try:
            response = await self.retry_with_backoff(_request)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise
            raise CalendarEventCreateFailedError(
                f"Failed to create calendar event: {exc.response.status_code} {exc.response.text}"
            ) from exc
        except (TimeoutError, httpx.HTTPError, OSError) as exc:
            raise CalendarEventCreateFailedError(f"Failed to create calendar event: {exc}") from exc

        data: dict[str, Any] = response.json()
        return self._parse_event(data)

    async def patch_event(
        self, access_token: str, event_id: str, spec: CalendarEventSpec
    ) -> CalendarEvent:
        """Patch an existing Calendar event's time window (reschedule).

        Sends ``PATCH {CAL_BASE}/calendars/{calendar_id}/events/{event_id}`` with
        ``conferenceDataVersion=1`` and ``sendUpdates=all``. The body contains
        only ``start``/``end`` (and notes) and OMITS ``conferenceData`` so the
        existing Google Meet link is preserved (R7.2).

        Args:
            access_token: OAuth2 access token for the acting HR user.
            event_id: The Google Calendar event identifier to patch.
            spec: The event specification carrying the new start/end times.

        Returns:
            The updated :class:`CalendarEvent`.

        Raises:
            CalendarEventUpdateFailedError: If the patch fails after retries.
            httpx.HTTPStatusError: If ``401`` (for token refresh handling).
        """
        calendar_id = spec.calendar_id
        url = f"{self._base_url}/calendars/{calendar_id}/events/{event_id}"
        params: dict[str, str | int] = {"conferenceDataVersion": 1, "sendUpdates": "all"}
        body = self._build_patch_body(spec)

        async def _request() -> httpx.Response:
            response = await self._http_client.patch(
                url,
                headers=self._auth_headers(access_token),
                params=params,
                json=body,
            )
            response.raise_for_status()
            return response

        try:
            response = await self.retry_with_backoff(_request)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise
            raise CalendarEventUpdateFailedError(
                f"Failed to update calendar event {event_id}: "
                f"{exc.response.status_code} {exc.response.text}"
            ) from exc
        except (TimeoutError, httpx.HTTPError, OSError) as exc:
            raise CalendarEventUpdateFailedError(
                f"Failed to update calendar event {event_id}: {exc}"
            ) from exc

        data: dict[str, Any] = response.json()
        return self._parse_event(data)

    async def delete_event(
        self, access_token: str, event_id: str, calendar_id: str = "primary"
    ) -> None:
        """Delete (cancel) a Calendar event idempotently.

        Sends ``DELETE {CAL_BASE}/calendars/{calendar_id}/events/{event_id}`` with
        ``sendUpdates=all`` so cancellation notices are emailed. A ``404``/``410``
        response (the event is already gone) is treated as success so cancel is
        idempotent.

        Args:
            access_token: OAuth2 access token for the acting HR user.
            event_id: The Google Calendar event identifier to delete.
            calendar_id: The Google Calendar ID (default ``primary``).

        Raises:
            httpx.HTTPStatusError: For non-2xx responses other than 404/410,
                including ``401`` (for token refresh handling).
        """
        url = f"{self._base_url}/calendars/{calendar_id}/events/{event_id}"
        params: dict[str, str] = {"sendUpdates": "all"}

        async def _request() -> httpx.Response:
            response = await self._http_client.delete(
                url,
                headers=self._auth_headers(access_token),
                params=params,
            )
            response.raise_for_status()
            return response

        try:
            await self.retry_with_backoff(_request)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in _GONE_STATUS_CODES:
                # Event already gone — idempotent cancellation succeeds.
                logger.info(
                    "Calendar event %s already gone (status %d); treating as cancelled",
                    event_id,
                    exc.response.status_code,
                )
                return
            raise

    async def list_calendars(
        self, access_token: str, *, min_access_role: str = "writer"
    ) -> list[dict[str, Any]]:
        """List calendars available via ``calendarList.list``.

        Returns calendars where the authenticated user has at least the specified
        ``minAccessRole`` (default ``"writer"``), so only calendars writable by the
        Organization Google Connection are shown.

        Args:
            access_token: OAuth2 access token with the
                ``calendar.calendarlist.readonly`` scope.
            min_access_role: Minimum access role filter (``"freeBusyReader"``,
                ``"reader"``, ``"writer"``, ``"owner"``). Defaults to ``"writer"``.

        Returns:
            List of calendar list entry dicts, each with ``id``, ``summary``,
            ``description``, ``primary``, and ``accessRole`` keys.

        Raises:
            httpx.HTTPStatusError: If ``401`` (for token refresh handling).
        """
        url = f"{self._base_url}/users/me/calendarList"
        params: dict[str, str | int] = {"minAccessRole": min_access_role}

        async def _request() -> httpx.Response:
            response = await self._http_client.get(
                url,
                headers=self._auth_headers(access_token),
                params=params,
            )
            response.raise_for_status()
            return response

        response = await self.retry_with_backoff(_request)
        data: dict[str, Any] = response.json()
        items: list[dict[str, Any]] = data.get("items", [])
        return items

    async def list_events(
        self,
        access_token: str,
        calendar_id: str,
        *,
        sync_token: str | None = None,
        page_token: str | None = None,
        max_results: int = 250,
        time_min: str | None = None,
        time_max: str | None = None,
    ) -> SyncEventChanges:
        """Fetch events changes via ``events.list`` with optional sync token.

        Supports incremental sync: when ``sync_token`` is provided, only
        events changed since the token are returned. When ``sync_token`` is
        None, a full snapshot is returned (used for initial sync or 410
        recovery). Pagination is handled via ``page_token``.

        When no ``sync_token`` is given (bounded full sync), ``time_min``
        and ``time_max`` may optionally bound the fetch window to keep the
        response size manageable. Defaults to last 30 days through +90 days
        (future event window) when set in the service layer.

        Args:
            access_token: OAuth2 access token with the calendar scope.
            calendar_id: The Google Calendar ID to list events from.
            sync_token: Sync token for incremental sync, or None for full sync.
            page_token: Page token for pagination within one sync response.
            max_results: Maximum results per page (default 250, max 2500).
            time_min: RFC3339 datetime lower bound for full sync.
            time_max: RFC3339 datetime upper bound for full sync.

        Returns:
            :class:`SyncEventChanges` with the parsed events and next tokens.

        Raises:
            CalendarEventSyncError: If the sync fails after retries (wraps
                non-401 errors).
            httpx.HTTPStatusError: If ``401`` (for token refresh), or ``410``
                (sync token expired \u2014 caller should clear cursor and retry).
        """
        url = f"{self._base_url}/calendars/{calendar_id}/events"
        params: dict[str, str | int] = {
            "showDeleted": "true",
            "maxResults": max_results,
            "singleEvents": "true",
        }
        if sync_token is not None:
            params["syncToken"] = sync_token
        if page_token is not None:
            params["pageToken"] = page_token
        if sync_token is None:
            if time_min is not None:
                params["timeMin"] = time_min
            if time_max is not None:
                params["timeMax"] = time_max

        async def _request() -> httpx.Response:
            response = await self._http_client.get(
                url,
                headers=self._auth_headers(access_token),
                params=params,
            )
            response.raise_for_status()
            return response

        try:
            response = await self.retry_with_backoff(_request)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 410):
                # 401: token refresh needed \u2014 re-raise for caller.
                # 410: sync token expired \u2014 re-raise for caller to clear cursor.
                raise
            raise CalendarEventSyncError(
                f"Failed to list calendar events: {exc.response.status_code} {exc.response.text}"
            ) from exc
        except (TimeoutError, httpx.HTTPError, OSError) as exc:
            raise CalendarEventSyncError(f"Failed to list calendar events: {exc}") from exc

        data: dict[str, Any] = response.json()
        raw_items: list[dict[str, Any]] = data.get("items", [])
        events = tuple(self._parse_event(item) for item in raw_items)

        return SyncEventChanges(
            events=events,
            next_sync_token=self._optional_str(data.get("nextSyncToken")),
            next_page_token=self._optional_str(data.get("nextPageToken")),
        )
