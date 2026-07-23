"""Property 9: a successful schedule always requests a Google Meet link.

Feature: interview-calendar-scheduling, Property 9.

Validates: Requirements 6.1 - WHEN the Scheduling_System creates the Google
Calendar event for a Candidate's interview, THE Scheduling_System SHALL request a
Google Meet conferencing link for that event.

The property is exercised end to end against the in-memory seams in
``_interview_support``: a fake ``CalendarPort`` records the
:class:`CalendarEventSpec` the service hands to the adapter
(``harness.calendar.create_calls[0].spec``), an in-memory candidate
repository/session backs persistence, and the module-level ``log_audit`` is
replaced by the spy sink (the real helper would call ``session.add``/``flush``,
which the fake session does not implement).

For every valid, successful schedule (permitting status, valid grant, 1..10
matching interviewers, future start, valid duration, optional notes) the created
event spec must have ``request_meet_link is True`` - i.e. the service always asks
the Calendar adapter to attach a Google Meet link.
"""

# Feature: interview-calendar-scheduling, Property 9

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.recruitment.application import interview_scheduler_service as candidate_service
from src.modules.recruitment.application.candidate_validators import VALID_TRANSITIONS
from src.modules.recruitment.domain.enums import CandidateStatus
from tests.modules.recruitment._interview_support import (
    build_calendar_harness,
    make_candidate,
    make_employee,
)

# Statuses from which a transition to ``interview_scheduled`` IS allowed, derived
# from the live state machine so the set tracks the source of truth.
# Resolves to: new, reviewing.
PERMITTING_STATUSES: list[str] = [
    status
    for status in CandidateStatus
    if CandidateStatus.INTERVIEW_SCHEDULED in VALID_TRANSITIONS.get(status, set())
]


# Feature: interview-calendar-scheduling, Property 9
@settings(max_examples=100, deadline=None)
@given(
    status=st.sampled_from(PERMITTING_STATUSES),
    duration_minutes=st.integers(min_value=15, max_value=180),
    interviewer_count=st.integers(min_value=1, max_value=10),
    start_offset_minutes=st.integers(min_value=1, max_value=60 * 24 * 365),
    notes=st.none() | st.text(max_size=1000),
)
def test_successful_schedule_always_requests_meet_link(
    status: str,
    duration_minutes: int,
    interviewer_count: int,
    start_offset_minutes: int,
    notes: str | None,
) -> None:
    """Every successful schedule builds a create spec that requests a Meet link.

    For any Candidate in a permitting status with a valid Calendar grant and a
    valid request, ``schedule_interview`` succeeds and the single
    ``CalendarEventSpec`` sent to the adapter has ``request_meet_link is True``.

    Validates: Requirements 6.1
    """

    async def _run() -> None:
        # Distinct interviewer emails so attendee resolution never fails and the
        # schedule reaches the Calendar create call.
        employees = [
            make_employee(email=f"interviewer{i}@example.com") for i in range(interviewer_count)
        ]
        interviewer_ids: list[UUID] = [employee.id for employee in employees]

        candidate = make_candidate(status=status)
        harness = build_calendar_harness(candidates=[candidate], employees=employees)

        # A valid, future start so request-field validation (R1.4) passes.
        start = datetime.now(UTC) + timedelta(minutes=start_offset_minutes)

        # The real ``log_audit`` would hit ``session.add``/``flush`` (unsupported
        # by the fake session); the spy sink records entries without persisting.
        with patch.object(candidate_service, "log_audit", harness.audit_sink):
            await harness.service.schedule_interview(
                candidate.id,
                start=start,
                duration_minutes=duration_minutes,
                interviewer_ids=interviewer_ids,
                notes=notes,
            )

        # A successful schedule builds exactly one create-event spec.
        assert len(harness.calendar.create_calls) == 1
        spec = harness.calendar.create_calls[0].spec
        assert spec is not None

        # R6.1: the create spec always requests a Google Meet conferencing link.
        assert spec.request_meet_link is True

    asyncio.run(_run())
