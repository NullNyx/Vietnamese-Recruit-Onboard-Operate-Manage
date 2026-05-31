"""Property 10: a successful schedule persists references and audits the action.

Feature: interview-calendar-scheduling, Property 10.

Validates: Requirements 2.1, 2.3, 4.1, 4.2, 4.3, 12.1.

For any Candidate in a permitting status (``new``/``reviewing``) with a valid
Calendar grant and a valid Schedule_Interview_Request, when the Calendar adapter
confirms event creation, ``CandidateService.schedule_interview``:

* invokes the adapter exactly once with the acting HR user's *decrypted* OAuth
  access token (R2.1 — the Calendar event is created via the adapter using the
  acting HR user's token);
* transitions the Candidate to ``interview_scheduled`` (R2.3);
* stores the returned ``calendar_event_id`` (R4.1), the scheduled ``start`` as a
  well-defined instant (R4.2), and the applied Organization timezone (R4.3); and
* writes an audit entry recording the schedule action, the acting HR user, the
  Candidate id, and the ``calendar_event_id`` (R12.1).

The property is exercised end to end against the in-memory seams in
``_interview_support``: a fake ``CalendarPort`` records each adapter call
(method, access token, and spec) and returns a scripted/default
:class:`CalendarEvent`; an in-memory candidate repository/session backs
persistence; the identity-side cipher decrypts ``enc:tok-access`` -> ``tok-access``;
and the module-level ``log_audit`` is replaced by the spy sink (the real helper
would call ``session.add``/``flush``, which the fake session does not implement).

Starts are drawn as tz-aware UTC datetimes far in the future so the future-``start``
rule (R1.4) always passes while the requested instant stays well-defined; the
timezone the service applies is checked instant-for-instant (tz-robust).
"""

# Feature: interview-calendar-scheduling, Property 10

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import UUID

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.recruitment.application import candidate_service
from src.modules.recruitment.domain.enums import CandidateStatus
from tests.modules.recruitment._interview_support import (
    build_calendar_harness,
    iana_timezones,
    make_candidate,
    make_employee,
)

# The decrypted access token the adapter must receive. ``make_oauth_grant``
# defaults ``access_token_enc="enc:tok-access"`` and ``FakeTokenCipher`` strips
# the ``"enc:"`` prefix, so the token handed to the adapter is ``"tok-access"``.
_EXPECTED_ACCESS_TOKEN = "tok-access"

# Statuses from which a transition to ``interview_scheduled`` is permitted.
_PERMITTING_STATUSES = st.sampled_from([CandidateStatus.NEW, CandidateStatus.REVIEWING])
# Valid, unambiguously-future starts: tz-aware UTC datetimes far in the future
# (well beyond any execution-time clock skew), so R1.4 always passes while the
# requested instant stays well-defined.
_FUTURE_START = st.datetimes(
    min_value=datetime(2090, 1, 1, 0, 0, 0),
    max_value=datetime(2099, 12, 31, 23, 59, 59),
    timezones=st.just(UTC),
)
# Valid durations span the inclusive 15..180 minute range (R1.2).
_DURATIONS = st.integers(min_value=15, max_value=180)
# Valid interviewer counts span the inclusive 1..10 range (R1.3).
_INTERVIEWER_COUNTS = st.integers(min_value=1, max_value=10)


@settings(max_examples=100, deadline=None)
@given(
    status=_PERMITTING_STATUSES,
    start=_FUTURE_START,
    duration_minutes=_DURATIONS,
    interviewer_count=_INTERVIEWER_COUNTS,
    org_timezone=iana_timezones(),
    notes=st.none() | st.text(max_size=1000),
)
def test_successful_schedule_persists_references_and_audits(
    status: str,
    start: datetime,
    duration_minutes: int,
    interviewer_count: int,
    org_timezone: str,
    notes: str | None,
) -> None:
    """A confirmed create persists the event reference/start/timezone and audits.

    Validates: Requirements 2.1, 2.3, 4.1, 4.2, 4.3, 12.1
    """

    async def _run() -> None:
        employees = [
            make_employee(email=f"interviewer{i}@example.com") for i in range(interviewer_count)
        ]
        interviewer_ids: list[UUID] = [employee.id for employee in employees]

        candidate = make_candidate(status=status)
        harness = build_calendar_harness(
            candidates=[candidate],
            employees=employees,
            org_timezone=org_timezone,
        )

        # The real ``log_audit`` would hit ``session.add``/``flush`` (unsupported
        # by the fake session); the spy sink records entries without persisting.
        with patch.object(candidate_service, "log_audit", harness.audit_sink):
            returned = await harness.service.schedule_interview(
                candidate.id,
                start=start,
                duration_minutes=duration_minutes,
                interviewer_ids=interviewer_ids,
                notes=notes,
            )

        # R2.1: the adapter is invoked exactly once, with the acting HR user's
        # decrypted access token.
        assert len(harness.calendar.create_calls) == 1
        create_call = harness.calendar.create_calls[0]
        assert create_call.access_token == _EXPECTED_ACCESS_TOKEN
        assert create_call.access_token == harness.crypto.decrypt("enc:tok-access")

        # R2.3: the Candidate transitions to ``interview_scheduled``.
        assert returned.status == CandidateStatus.INTERVIEW_SCHEDULED

        # R4.1: the returned Calendar event id is stored as ``calendar_event_id``.
        assert returned.calendar_event_id is not None

        # The committed Candidate carries the same persisted references (the
        # service committed before returning).
        persisted = await harness.candidate_repo.get_by_id(candidate.id)
        assert persisted is not None
        assert persisted.status == CandidateStatus.INTERVIEW_SCHEDULED
        assert persisted.calendar_event_id == returned.calendar_event_id
        # R4.2: the stored start equals the requested start instant (tz-robust:
        # the service expresses it in the org timezone but the instant is fixed).
        assert persisted.interview_start_at is not None
        assert persisted.interview_start_at.astimezone(UTC) == start.astimezone(UTC)
        # R4.3: the stored timezone is the Organization's configured timezone.
        assert persisted.interview_timezone == org_timezone

        # R12.1: an audit entry records the schedule action, the acting HR user,
        # the Candidate id, and the ``calendar_event_id``.
        scheduled_entries = harness.audit_sink.entries_for("interview_scheduled")
        assert len(scheduled_entries) == 1
        entry = scheduled_entries[0]
        assert entry.user_id == harness.user_id
        assert entry.entity_id == candidate.id
        assert entry.success is True
        assert entry.new_value is not None
        assert entry.new_value["calendar_event_id"] == persisted.calendar_event_id

    asyncio.run(_run())
