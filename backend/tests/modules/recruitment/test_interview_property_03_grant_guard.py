"""Property test for the Calendar grant guard (Property 3).

Feature: interview-calendar-scheduling, Property 3

Property 3 — Calendar grant guard:
    For any schedule or reschedule request, if the acting HR user's
    ``calendar_grant_valid`` is false, the request is rejected with a
    re-consent error (``CalendarGrantMissingError``), the Candidate record is
    left unchanged, and the Calendar adapter is never invoked.

The grant is made invalid two ways, both exercised by Hypothesis:

* ``granted_scopes=()`` — a grant that exists but lacks the Calendar scope, so
  ``OAuthService.determine_grant_status`` reports ``calendar_grant_valid`` false.
* ``grant=None`` — no grant at all (modelled as missing).

``schedule_interview`` asserts the grant (step 3) *after* request-field
validation and the status-transition check but *before* resolving interviewers
or touching the Calendar adapter, so every generated request uses valid fields
and a permitting Candidate status to ensure the grant guard is the rule under
test. The reschedule case is guarded with ``skipif`` because
``reschedule_interview`` lands in task 7.1; it seeds a Candidate that already
has a stored ``calendar_event_id``/``interview_start_at`` so the request reaches
the grant assertion rather than the "no interview to reschedule" check.

Validates: Requirements 9.1, 9.2, 9.3
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.employee.domain.entities import Employee
from src.modules.recruitment.application.candidate_service import CandidateService
from src.modules.recruitment.domain.enums import CandidateStatus
from src.modules.recruitment.domain.exceptions import CalendarGrantMissingError
from tests.modules.recruitment._interview_support import (
    build_calendar_harness,
    make_candidate,
    make_employee,
)

# Candidate statuses from which a transition to ``interview_scheduled`` is
# permitted (so the schedule request reaches the grant assertion, R9).
_PERMITTING_STATUSES = (CandidateStatus.NEW, CandidateStatus.REVIEWING)

# ``reschedule_interview`` is implemented in task 7.1; skip its property until
# the method exists so this file stays green on the schedule-only milestone.
_HAS_RESCHEDULE = hasattr(CandidateService, "reschedule_interview")


def _interviewers(count: int) -> list[Employee]:
    """Build ``count`` interviewer Employees with distinct, non-blank emails."""
    return [make_employee(email=f"interviewer{i}@example.com") for i in range(count)]


# ─── Property 3 (schedule path) — R9.1, R9.3 ───────────────────────────


@settings(max_examples=100, deadline=None)
@given(
    duration_minutes=st.integers(min_value=15, max_value=180),
    interviewer_count=st.integers(min_value=1, max_value=10),
    start_offset_minutes=st.integers(min_value=10, max_value=525_600),
    use_none_grant=st.booleans(),
    status=st.sampled_from(_PERMITTING_STATUSES),
    notes=st.one_of(st.none(), st.text(max_size=1000)),
)
def test_schedule_blocked_when_calendar_grant_missing(
    duration_minutes: int,
    interviewer_count: int,
    start_offset_minutes: int,
    use_none_grant: bool,
    status: str,
    notes: str | None,
) -> None:
    """A missing Calendar grant blocks scheduling without touching the adapter.

    For any valid schedule request and any permitting Candidate status, when the
    acting HR user's ``calendar_grant_valid`` is false the request is rejected
    with a re-consent ``CalendarGrantMissingError`` (403 /
    ``CALENDAR_GRANT_MISSING``), the Calendar adapter is never invoked, and the
    Candidate record is left exactly as it was.

    Validates: Requirements 9.1, 9.3
    """

    async def _run() -> None:
        candidate = make_candidate(status=status)
        interviewers = _interviewers(interviewer_count)

        # Two ways to make ``calendar_grant_valid`` false: a grant lacking the
        # Calendar scope, or no grant at all.
        if use_none_grant:
            harness = build_calendar_harness(
                candidates=[candidate], employees=interviewers, grant=None
            )
        else:
            harness = build_calendar_harness(
                candidates=[candidate], employees=interviewers, granted_scopes=()
            )

        before = harness.candidate_repo.committed_snapshot(candidate.id)
        start = datetime.now(UTC) + timedelta(minutes=start_offset_minutes)

        with pytest.raises(CalendarGrantMissingError) as exc_info:
            await harness.service.schedule_interview(
                candidate.id,
                start=start,
                duration_minutes=duration_minutes,
                interviewer_ids=[e.id for e in interviewers],
                notes=notes,
            )

        # The error directs the user to re-consent (R9.1).
        assert exc_info.value.error_code == "CALENDAR_GRANT_MISSING"
        assert exc_info.value.status_code == 403

        # The Calendar adapter was never invoked (R9.3).
        assert harness.calendar.was_called is False
        assert harness.calendar.calls == []

        # The Candidate record is left unchanged (R9.3): the committed snapshot
        # is identical and the live entity carries no interview references, and
        # no transaction was committed or rolled back.
        after = harness.candidate_repo.committed_snapshot(candidate.id)
        assert after == before
        live = await harness.candidate_repo.get_by_id(candidate.id)
        assert live is not None
        assert live.status == status
        assert live.calendar_event_id is None
        assert live.interview_start_at is None
        assert live.interview_timezone is None
        assert harness.session.commit_count == 0
        assert harness.session.rollback_count == 0

    asyncio.run(_run())


# ─── Property 3 (reschedule path) — R9.2, R9.3 ─────────────────────────


@pytest.mark.skipif(
    not _HAS_RESCHEDULE,
    reason="reschedule_interview is implemented in task 7.1; grant guard covered there",
)
@settings(max_examples=100, deadline=None)
@given(
    duration_minutes=st.integers(min_value=15, max_value=180),
    interviewer_count=st.integers(min_value=1, max_value=10),
    start_offset_minutes=st.integers(min_value=10, max_value=525_600),
    use_none_grant=st.booleans(),
    notes=st.one_of(st.none(), st.text(max_size=1000)),
)
def test_reschedule_blocked_when_calendar_grant_missing(
    duration_minutes: int,
    interviewer_count: int,
    start_offset_minutes: int,
    use_none_grant: bool,
    notes: str | None,
) -> None:
    """A missing Calendar grant blocks rescheduling without touching the adapter.

    For any reschedule request against a Candidate that already has a stored
    interview, when the acting HR user's ``calendar_grant_valid`` is false the
    request is rejected with a re-consent ``CalendarGrantMissingError``, the
    Calendar adapter is never invoked, and the stored ``calendar_event_id`` and
    scheduled ``interview_start_at`` are left unchanged.

    Validates: Requirements 9.2, 9.3
    """

    async def _run() -> None:
        existing_event_id = "evt-existing-0001"
        existing_start = datetime(2025, 6, 1, 9, 0, tzinfo=UTC)
        candidate = make_candidate(
            status=CandidateStatus.INTERVIEW_SCHEDULED,
            calendar_event_id=existing_event_id,
            interview_start_at=existing_start,
            interview_timezone="Asia/Ho_Chi_Minh",
        )
        interviewers = _interviewers(interviewer_count)

        if use_none_grant:
            harness = build_calendar_harness(
                candidates=[candidate], employees=interviewers, grant=None
            )
        else:
            harness = build_calendar_harness(
                candidates=[candidate], employees=interviewers, granted_scopes=()
            )

        before = harness.candidate_repo.committed_snapshot(candidate.id)
        start = datetime.now(UTC) + timedelta(minutes=start_offset_minutes)

        with pytest.raises(CalendarGrantMissingError) as exc_info:
            await harness.service.reschedule_interview(
                candidate.id,
                start=start,
                duration_minutes=duration_minutes,
                interviewer_ids=[e.id for e in interviewers],
                notes=notes,
            )

        assert exc_info.value.error_code == "CALENDAR_GRANT_MISSING"
        assert exc_info.value.status_code == 403

        # The Calendar adapter was never invoked (R9.3).
        assert harness.calendar.was_called is False
        assert harness.calendar.calls == []

        # The stored interview references are left unchanged (R9.3).
        after = harness.candidate_repo.committed_snapshot(candidate.id)
        assert after == before
        live = await harness.candidate_repo.get_by_id(candidate.id)
        assert live is not None
        assert live.status == CandidateStatus.INTERVIEW_SCHEDULED
        assert live.calendar_event_id == existing_event_id
        assert live.interview_start_at == existing_start
        assert harness.session.commit_count == 0
        assert harness.session.rollback_count == 0

    asyncio.run(_run())
