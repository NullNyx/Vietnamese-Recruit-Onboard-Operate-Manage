"""Property 6: Event time window invariant (interview-calendar scheduling).

For any valid ``start`` and ``duration_minutes``, the :class:`CalendarEventSpec`
that :meth:`CandidateService.schedule_interview` builds and hands to the Calendar
adapter has its start equal to the requested ``start`` and its end equal to
``start`` plus ``duration_minutes`` -- hence the end is strictly after the start.

The property is exercised end to end against the in-memory seams in
``_interview_support``: a fake ``CalendarPort`` records the spec the service
builds (``harness.calendar.create_calls[0].spec``), an in-memory candidate
repository/session backs persistence, and the module-level ``log_audit`` is
replaced by the spy sink (the real helper would call ``session.add``/``flush``,
which the fake session does not implement).

``schedule_interview`` makes the event start/end tz-aware in the Organization
timezone: an aware ``start`` is converted with ``astimezone`` (preserving the
instant), so the assertions are written in a tz-robust way -- the duration is
checked as ``end - start`` and the start is compared as an absolute UTC instant.
Starts are therefore drawn as tz-aware UTC datetimes so the requested instant is
well-defined.

Validates: Requirements 2.2
"""

# Feature: interview-calendar-scheduling, Property 6

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.recruitment.application import candidate_service
from src.modules.recruitment.domain.enums import CandidateStatus
from tests.modules.recruitment._interview_support import (
    build_calendar_harness,
    make_candidate,
    make_employee,
)

# Valid, unambiguously-future starts: tz-aware UTC datetimes far in the future
# (well beyond any execution-time clock skew), so the service's future-``start``
# rule (R1.4) always passes while the requested instant stays well-defined.
_FUTURE_START = st.datetimes(
    min_value=datetime(2090, 1, 1, 0, 0, 0),
    max_value=datetime(2099, 12, 31, 23, 59, 59),
    timezones=st.just(UTC),
)
# Valid durations span the inclusive 15..180 minute range (R1.2).
_DURATIONS = st.integers(min_value=15, max_value=180)


@settings(max_examples=100, deadline=None)
@given(start=_FUTURE_START, duration_minutes=_DURATIONS)
def test_event_time_window_invariant(start: datetime, duration_minutes: int) -> None:
    """The built event spec has start == requested start and end == start + duration.

    Validates: Requirements 2.2
    """

    async def _run() -> None:
        interviewer = make_employee(email="interviewer@example.com")
        candidate = make_candidate(status=CandidateStatus.NEW)
        harness = build_calendar_harness(
            candidates=[candidate],
            employees=[interviewer],
            org_timezone="Asia/Ho_Chi_Minh",
        )

        # The real ``log_audit`` would hit ``session.add``/``flush`` (unsupported
        # by the fake session); the spy sink records entries without persisting.
        with patch.object(candidate_service, "log_audit", harness.audit_sink):
            await harness.service.schedule_interview(
                candidate.id,
                start=start,
                duration_minutes=duration_minutes,
                interviewer_ids=[interviewer.id],
                notes=None,
            )

        # A successful schedule builds exactly one create-event spec.
        assert len(harness.calendar.create_calls) == 1
        spec = harness.calendar.create_calls[0].spec
        assert spec is not None

        # end - start equals the requested duration (tz-robust: independent of the
        # org timezone the service applies).
        assert spec.end - spec.start == timedelta(minutes=duration_minutes)
        # Therefore the end is strictly after the start (durations are >= 15 min).
        assert spec.end > spec.start
        # The spec start is the requested start instant (same absolute UTC instant,
        # regardless of the timezone the service expresses it in).
        assert spec.start.astimezone(UTC) == start.astimezone(UTC)

    asyncio.run(_run())
