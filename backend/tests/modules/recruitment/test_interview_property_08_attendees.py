"""Property 8: attendee set equals Candidate plus interviewers.

For any Candidate and any valid interviewer set, the attendee email set on the
created Google Calendar event equals the union of the Candidate's email and every
interviewer Employee's email (Requirements 5.1, 5.2).

The orchestration is exercised end to end against the in-memory seams in
``_interview_support``: a fake ``CalendarPort`` records the
:class:`CalendarEventSpec` the service builds
(``harness.calendar.create_calls[0].spec.attendee_emails``), an in-memory
candidate repository/session backs persistence, and the module-level
``log_audit`` is replaced by the spy sink (the real helper would call
``session.add``/``flush``, which the fake session does not implement).

``CandidateService._build_attendees`` combines the Candidate email with the
interviewer emails, dropping blanks and removing case-insensitive duplicates
while preserving first-seen order. The property therefore compares *normalized*
(stripped, lower-cased) sets: the case-insensitive set of attendee emails on the
spec must equal the case-insensitive union of the Candidate email and every
interviewer email. Interviewer emails are always non-blank here (the blank-email
case is Property 4); some interviewers deliberately reuse the Candidate email or
another interviewer's email (with varied casing) to exercise the de-duplication.

Validates: Requirements 5.1, 5.2
"""

# Feature: interview-calendar-scheduling, Property 8

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.recruitment.application import interview_scheduler_service as candidate_service
from src.modules.recruitment.domain.enums import CandidateStatus
from tests.modules.recruitment._interview_support import (
    build_calendar_harness,
    make_candidate,
    make_employee,
)

# Statuses from which a transition to ``interview_scheduled`` is permitted, so
# the request reaches Calendar creation rather than being blocked by the state
# machine (R2.4).
PERMITTING_STATUSES = (CandidateStatus.NEW, CandidateStatus.REVIEWING)


def _norm(email: str) -> str:
    """Normalize an email the way ``_build_attendees`` de-duplicates: strip + lower."""
    return email.strip().lower()


def _apply_case(draw: st.DrawFn, value: str) -> str:
    """Return ``value`` re-cased in one of a few ways, to vary casing for de-dup."""
    mode = draw(st.sampled_from(("same", "lower", "upper", "swap")))
    if mode == "lower":
        return value.lower()
    if mode == "upper":
        return value.upper()
    if mode == "swap":
        return value.swapcase()
    return value


@st.composite
def _candidate_and_interviewers(
    draw: st.DrawFn,
) -> tuple[str, list[Employee], list[str]]:
    """Draw a Candidate email plus 1-10 interviewer Employees with valid emails.

    Each interviewer gets a non-blank email that is either freshly unique, a
    re-cased copy of the Candidate's email, or a re-cased copy of an earlier
    interviewer's email. Reusing emails (with varied casing) exercises the
    service's case-insensitive de-duplication while keeping every interviewer
    invitable (the blank-email case belongs to Property 4).

    Returns:
        A tuple ``(candidate_email, employees, interviewer_emails)`` where
        ``employees`` are the seeded interviewer Employees and
        ``interviewer_emails`` are their emails in the same order.
    """
    candidate_email = f"candidate-{draw(st.uuids()).hex[:10]}@example.com"

    count = draw(st.integers(min_value=1, max_value=10))
    employees: list[Employee] = []
    interviewer_emails: list[str] = []
    for index in range(count):
        source = draw(st.sampled_from(("fresh", "fresh", "candidate", "reuse")))
        if source == "candidate":
            base = candidate_email
        elif source == "reuse" and interviewer_emails:
            base = draw(st.sampled_from(interviewer_emails))
        else:
            base = f"interviewer-{index}-{draw(st.uuids()).hex[:10]}@example.com"

        email = _apply_case(draw, base)
        interviewer_emails.append(email)
        employees.append(make_employee(email=email, full_name=f"Interviewer {index}"))

    return candidate_email, employees, interviewer_emails


@settings(max_examples=100, deadline=None)
@given(
    data=_candidate_and_interviewers(),
    status=st.sampled_from(PERMITTING_STATUSES),
    duration_minutes=st.integers(min_value=15, max_value=180),
    start_offset_minutes=st.integers(min_value=1, max_value=60 * 24 * 365),
    notes=st.none() | st.text(max_size=1000),
)
def test_attendee_set_equals_candidate_plus_interviewers(
    data: tuple[str, list[Employee], list[str]],
    status: CandidateStatus,
    duration_minutes: int,
    start_offset_minutes: int,
    notes: str | None,
) -> None:
    """The created event's attendee set is the Candidate email plus interviewers.

    For any Candidate and any valid (non-blank) interviewer set, the
    case-insensitive set of attendee emails on the created event equals the
    case-insensitive union of the Candidate email and every interviewer email;
    the Candidate and each interviewer are present, and no duplicates remain.

    Validates: Requirements 5.1, 5.2
    """
    candidate_email, employees, interviewer_emails = data

    async def _run() -> None:
        candidate = make_candidate(status=status, email=candidate_email)
        harness = build_calendar_harness(
            candidates=[candidate],
            employees=employees,
        )
        # Strictly-future, tz-aware start so request-field validation (R1.4)
        # passes and the flow reaches Calendar creation.
        start = datetime.now(UTC) + timedelta(minutes=start_offset_minutes)

        with patch.object(candidate_service, "log_audit", harness.audit_sink):
            await harness.service.schedule_interview(
                candidate.id,
                start=start,
                duration_minutes=duration_minutes,
                interviewer_ids=[employee.id for employee in employees],
                notes=notes,
            )

        # A successful schedule builds exactly one create-event spec.
        assert len(harness.calendar.create_calls) == 1
        spec = harness.calendar.create_calls[0].spec
        assert spec is not None

        actual = {_norm(email) for email in spec.attendee_emails}
        expected = {_norm(candidate_email)} | {_norm(email) for email in interviewer_emails}

        # R5.1 + R5.2: the attendee set is exactly the Candidate plus every
        # interviewer, compared case-insensitively (the service de-dupes).
        assert actual == expected
        # R5.1: the Candidate is an attendee.
        assert _norm(candidate_email) in actual
        # R5.2: every interviewer is an attendee.
        assert all(_norm(email) in actual for email in interviewer_emails)
        # De-duplication: no normalized email appears twice on the event.
        assert len(spec.attendee_emails) == len(actual)

    asyncio.run(_run())
