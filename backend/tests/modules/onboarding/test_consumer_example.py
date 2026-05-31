"""Example tests for the onboarding ARQ consumer retry / rejection auditing.

These are EXAMPLE tests (not Hypothesis property tests). They pin down three
concrete behaviors of the consumer side of the onboarding module:

1. ``OnboardingWorkerSettings.max_tries == 3`` — the worker bounds per-job
   retries at three so transient failures are retried up to three times before
   the consumer records the final failure (R1.7). The consumer's own fallback
   constant ``container._MAX_TRIES`` is also asserted to equal 3 so the
   final-attempt detection still works when ARQ does not place ``max_tries`` in
   the job ``ctx``.
2. A malformed ``candidate_accepted`` event is *rejected*: the consumer writes
   exactly one ``event_rejected`` audit entry (``success = False``), never
   invokes the :class:`OnboardingService` creation path, and returns without
   raising (R1.6, R2.6).
3. Retry exhaustion records a failure audit entry: while ``job_try`` is below
   ``max_tries`` a transient error re-raises with *no* ``event_failed`` audit
   entry (so ARQ retries), and on the final attempt (``job_try == max_tries``)
   the consumer writes exactly one ``event_failed`` audit entry
   (``success = False``) before re-raising (R1.7, R1.5).

The consumer is driven against in-memory fakes so the tests run as fast,
pure-logic checks. ``container._build_service`` is monkeypatched to a tracked
stand-in so we can assert whether the service was built/called and inject a
transient error, and ``container.OnboardingAuditRepository`` is monkeypatched to
a recording fake that captures every appended audit entry. A fake
``session_maker`` yields an ``async with``-capable session with a no-op
``commit``.

Validates: Requirements 1.6, 1.7, 2.6
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.onboarding import container
from src.modules.onboarding.container import (
    _MAX_TRIES,
    _OP_EVENT_FAILED,
    _OP_EVENT_REJECTED,
    process_candidate_accepted,
)
from src.modules.onboarding.domain.entities import OnboardingAuditLog
from src.modules.onboarding.worker import OnboardingWorkerSettings


# ---------------------------------------------------------------------------
# In-memory fakes (inline, self-contained)
# ---------------------------------------------------------------------------
class _FakeSession:
    """Minimal async session: ``async with`` support and a no-op ``commit``."""

    def __init__(self) -> None:
        self.commit_count = 0

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        return None


def _make_fake_session_maker() -> Callable[[], _FakeSession]:
    """Return a session factory yielding a fresh fake session per call."""

    def session_maker() -> _FakeSession:
        return _FakeSession()

    return session_maker


def _make_recording_audit_repo(
    captured: list[OnboardingAuditLog],
) -> Callable[[Any], Any]:
    """Build an ``OnboardingAuditRepository`` stand-in recording appends.

    Every instance shares the ``captured`` list so audit entries written across
    the consumer's separate sessions (rejection / failure each open their own)
    are collected in one place for assertions.
    """

    class _RecordingAuditRepo:
        def __init__(self, session: Any) -> None:
            self._session = session

        async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
            captured.append(entry)
            return entry

    return _RecordingAuditRepo


def _build_ctx(*, job_try: int, max_tries: int | None = None) -> dict[str, Any]:
    """Build an ARQ-style job context for the consumer."""
    ctx: dict[str, Any] = {
        "session_maker": _make_fake_session_maker(),
        "job_id": f"job-{uuid4().hex}",
        "job_try": job_try,
    }
    if max_tries is not None:
        ctx["max_tries"] = max_tries
    return ctx


def _valid_payload() -> dict[str, Any]:
    """A well-formed ``candidate_accepted`` payload."""
    return {
        "candidate_id": str(uuid4()),
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_max_tries_is_three() -> None:
    """The worker bounds per-job retries at three (R1.7).

    Asserts both the worker setting (the value ARQ actually uses) and the
    consumer's fallback constant used for final-attempt detection when ARQ does
    not supply ``max_tries`` in the job ``ctx``.

    Validates: Requirements 1.7
    """
    assert OnboardingWorkerSettings.max_tries == 3
    assert _MAX_TRIES == 3


async def test_malformed_event_rejected_without_service_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A malformed event is rejected + audited, and never calls the service.

    With a payload missing ``email`` the consumer must reject the event: write
    exactly one ``event_rejected`` audit entry (``success = False``), never
    build/invoke the :class:`OnboardingService`, and return without raising
    (R1.6, R2.6).

    Validates: Requirements 1.6, 2.6
    """
    captured: list[OnboardingAuditLog] = []
    build_calls: list[Any] = []
    service = MagicMock()
    service.start_from_event = AsyncMock()

    def fake_build_service(session: Any) -> Any:
        build_calls.append(session)
        return service

    monkeypatch.setattr(container, "_build_service", fake_build_service)
    monkeypatch.setattr(
        container, "OnboardingAuditRepository", _make_recording_audit_repo(captured)
    )

    malformed_payload = {"candidate_id": str(uuid4()), "name": "Jane Doe"}  # no email
    ctx = _build_ctx(job_try=1, max_tries=3)

    # Must return (no raise) for a malformed event.
    result = await process_candidate_accepted(ctx, malformed_payload)
    assert result is None

    # The service was never built and start_from_event was never called.
    assert build_calls == []
    service.start_from_event.assert_not_called()

    # Exactly one rejection audit entry, marked as a failure.
    rejection_entries = [e for e in captured if e.operation_type == _OP_EVENT_REJECTED]
    assert len(rejection_entries) == 1
    assert rejection_entries[0].success is False
    assert rejection_entries[0].entity_type == "event"
    # No failure (retry-exhaustion) entry is written for a malformed event.
    assert not any(e.operation_type == _OP_EVENT_FAILED for e in captured)


async def test_retry_exhaustion_records_failure_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transient errors re-raise; only the final attempt audits the failure.

    For a valid payload whose service call raises a transient error: while
    ``job_try < max_tries`` the consumer re-raises with no ``event_failed``
    audit entry (ARQ will retry); on the final attempt (``job_try ==
    max_tries``) the consumer writes exactly one ``event_failed`` audit entry
    (``success = False``) and re-raises (R1.7, R1.5).

    Validates: Requirements 1.7
    """
    captured: list[OnboardingAuditLog] = []
    service = MagicMock()
    service.start_from_event = AsyncMock(side_effect=RuntimeError("transient db error"))

    monkeypatch.setattr(container, "_build_service", lambda session: service)
    monkeypatch.setattr(
        container, "OnboardingAuditRepository", _make_recording_audit_repo(captured)
    )

    payload = _valid_payload()

    # Attempt below the limit: re-raises, no failure audit (will be retried).
    early_ctx = _build_ctx(job_try=1, max_tries=3)
    with pytest.raises(RuntimeError, match="transient db error"):
        await process_candidate_accepted(early_ctx, payload)

    assert service.start_from_event.await_count == 1
    assert not any(e.operation_type == _OP_EVENT_FAILED for e in captured)

    # Final attempt (job_try == max_tries): records the failure, then re-raises.
    final_ctx = _build_ctx(job_try=3, max_tries=3)
    with pytest.raises(RuntimeError, match="transient db error"):
        await process_candidate_accepted(final_ctx, payload)

    assert service.start_from_event.await_count == 2
    failure_entries = [e for e in captured if e.operation_type == _OP_EVENT_FAILED]
    assert len(failure_entries) == 1
    assert failure_entries[0].success is False
    assert failure_entries[0].entity_type == "event"
