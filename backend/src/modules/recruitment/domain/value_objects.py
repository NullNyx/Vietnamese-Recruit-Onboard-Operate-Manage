"""Domain value objects for the Recruitment module.

Defines immutable value objects used throughout the application layer
for data transfer and validation. CV-pipeline data is modelled with
Pydantic ``BaseModel`` classes, while the calendar-scheduling I/O types
(``CalendarEventSpec`` and ``CalendarEvent``) are frozen dataclasses
per ADR-0008.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MeetingMode(StrEnum):
    """Mode for an interview meeting."""

    GOOGLE_MEET = "google_meet"
    IN_PERSON = "in_person"
    CUSTOM_LINK = "custom_link"


class ExperienceItem(BaseModel):
    """A single work experience entry extracted from a CV.

    Represents one position held by the candidate, including
    company name, job title, duration, and description.
    """

    company: str = Field(max_length=200)
    title: str = Field(max_length=200)
    duration: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=1000)


class EducationItem(BaseModel):
    """A single education entry extracted from a CV.

    Represents one educational qualification including institution,
    degree type, field of study, and graduation year.
    """

    institution: str = Field(max_length=200)
    degree: str = Field(default="", max_length=100)
    field: str = Field(default="", max_length=200)
    year: str = Field(default="", max_length=20)


class ParsedCV(BaseModel):
    """Structured data extracted from a CV via LLM parsing.

    Contains the key fields that the LLM extracts from OCR text,
    used to create or update Candidate records. Fields have maximum
    lengths to prevent storage issues and ensure data quality.
    """

    name: str = Field(max_length=200)
    email: str = Field(max_length=254)
    phone: str = Field(default="", max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=50)
    experience: list[ExperienceItem] = Field(default_factory=list, max_length=20)
    education: list[EducationItem] = Field(default_factory=list, max_length=10)
    summary: str = Field(default="", max_length=500)


@dataclass(frozen=True)
class CalendarEventSpec:
    """Input to the Calendar adapter (pure, timezone-resolved).

    Describes the Google Calendar event the Scheduling_System wants to
    create or patch. ``end`` is always derived by the service as
    ``start + timedelta(minutes=duration_minutes)``, so the invariant
    ``end == start + duration`` holds and, for the valid duration range
    (15-180 minutes), ``end`` is strictly after ``start``.

    Attributes:
        summary: Event title shown on the calendar.
        description: Optional event description (interview notes).
        start: Timezone-aware interview start datetime.
        end: Timezone-aware interview end datetime (``start + duration``).
        timezone: IANA timezone name applied to the event (e.g.
            ``"Asia/Ho_Chi_Minh"``).
        attendee_emails: De-duplicated attendee email addresses
            (Candidate + interviewer Employees).
        request_meet_link: Whether to request a Google Meet conferencing
            link for the event.
    """

    summary: str
    description: str | None
    start: datetime
    end: datetime
    timezone: str
    attendee_emails: tuple[str, ...]
    calendar_id: str = "primary"
    request_meet_link: bool = True

    def __post_init__(self) -> None:
        """Validate the event time-window invariant.

        Raises:
            ValueError: If ``start`` or ``end`` is not timezone-aware, or
                if ``end`` is not strictly after ``start``.
        """
        if self.start.tzinfo is None or self.start.utcoffset() is None:
            raise ValueError("CalendarEventSpec.start must be timezone-aware")
        if self.end.tzinfo is None or self.end.utcoffset() is None:
            raise ValueError("CalendarEventSpec.end must be timezone-aware")
        if self.end <= self.start:
            raise ValueError("CalendarEventSpec.end must be after start")


@dataclass(frozen=True)
class CalendarEvent:
    """Result returned by the Calendar adapter after a create, patch, or sync.

    Models the relevant parts of the Google Calendar API response so the
    Scheduling_System can persist the event reference on the Candidate.

    Attributes:
        event_id: Google Calendar event identifier.
        html_link: Link to view the event in Google Calendar, if returned.
        meet_link: Google Meet conferencing link, if one was generated.
        location: Physical location from the calendar event, if set.
        invited_emails: Attendee emails that Google accepted on the event.
        etag: ETag for optimistic concurrency.
        updated: RFC3339 update timestamp from Google.
        status: Event status ("confirmed", "cancelled", "tentative").
        attendees: Raw attendee list with "email", "responseStatus", etc.
    """

    event_id: str
    html_link: str | None
    meet_link: str | None
    location: str | None = None
    invited_emails: tuple[str, ...] = ()
    etag: str | None = None
    updated: datetime | None = None
    status: str | None = None
    attendees: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class SyncEventChanges:
    """Result returned by the Calendar adapter after a sync (events.list).

    Contains the list of changed events plus pagination/sync tokens.

    Attributes:
        events: Tuple of changed CalendarEvent objects.
        next_sync_token: Token for the next incremental sync.
        next_page_token: Token to paginate a single sync response.
    """

    events: tuple[CalendarEvent, ...] = ()
    next_sync_token: str | None = None
    next_page_token: str | None = None
