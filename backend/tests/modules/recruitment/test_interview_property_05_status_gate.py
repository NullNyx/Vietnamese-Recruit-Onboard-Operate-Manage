"""Property 5: a non-permitting Candidate status blocks interview scheduling.

Feature: interview-calendar-scheduling, Property 5.

Validates: Requirements 2.4 - if the Candidate's current status does not permit
a transition to ``interview_scheduled``, ``schedule_interview`` rejects the
request with a status-transition error and creates no Google Calendar event.

The status gate (``_validate_transition``) runs in step 2 of
``schedule_interview`` - after the request-field validation (step 1) but before
the Calendar grant check, interviewer resolution, and any Calendar adapter call.
This test therefore sends an otherwise *valid* request (good duration, future
start, a matching seeded interviewer) so the status is the only thing that can
fail, then asserts the adapter is never invoked.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.recruitment.application.candidate_validators import VALID_TRANSITIONS
from src.modules.recruitment.domain.enums import CandidateStatus
from src.modules.recruitment.domain.exceptions import InvalidStatusTransitionError
from tests.modules.recruitment._interview_support import (
    build_calendar_harness,
    make_candidate,
    make_employee,
)

# Statuses from which a transition to ``interview_scheduled`` is NOT allowed,
# derived from the live state machine so the set tracks the source of truth.
# Resolves to: interview_scheduled, accepted, rejected, archived.
NON_PERMITTING_STATUSES: list[str] = [
    status
    for status in CandidateStatus
    if CandidateStatus.INTERVIEW_SCHEDULED not in VALID_TRANSITIONS.get(status, set())
]


# Feature: interview-calendar-scheduling, Property 5
@settings(max_examples=100, deadline=None)
@given(
    status=st.sampled_from(NON_PERMITTING_STATUSES),
    duration_minutes=st.integers(min_value=15, max_value=180),
    interviewer_count=st.integers(min_value=1, max_value=10),
    start_offset_minutes=st.integers(min_value=1, max_value=60 * 24 * 365),
    notes=st.none() | st.text(max_size=1000),
)
def test_non_permitting_status_blocks_scheduling(
    status: str,
    duration_minutes: int,
    interviewer_count: int,
    start_offset_minutes: int,
    notes: str | None,
) -> None:
    """A schedule request on a non-permitting status raises and skips Calendar.

    For any Candidate whose status does not permit the transition to
    ``interview_scheduled``, ``schedule_interview`` raises
    ``InvalidStatusTransitionError`` and the Calendar adapter is never invoked.

    Validates: Requirements 2.4
    """

    async def _run() -> None:
        # Seed matching interviewer Employees so interviewer resolution (a later
        # step) cannot be the reason for failure - the status gate must be.
        employees = [
            make_employee(email=f"interviewer{i}@example.com") for i in range(interviewer_count)
        ]
        interviewer_ids: list[UUID] = [employee.id for employee in employees]

        candidate = make_candidate(status=status)
        harness = build_calendar_harness(candidates=[candidate], employees=employees)

        # A valid, future start so step-1 request validation passes and the
        # status gate (step 2) is the only failing check.
        start = datetime.now(UTC) + timedelta(minutes=start_offset_minutes)

        with pytest.raises(InvalidStatusTransitionError):
            await harness.service.schedule_interview(
                candidate.id,
                start=start,
                duration_minutes=duration_minutes,
                interviewer_ids=interviewer_ids,
                notes=notes,
            )

        # R2.4: no Google Calendar event is created on a non-permitting status.
        assert harness.calendar.was_called is False

    asyncio.run(_run())
