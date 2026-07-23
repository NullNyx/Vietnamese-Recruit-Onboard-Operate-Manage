"""Shared pytest fixtures for the recruitment test suite.

Re-exports the interview-calendar property-test seams from
``_interview_support`` as pytest fixtures so the property tests for tasks
5.2-5.13, 7.x, 8.x, and 10.x can request them directly. The seams themselves
live in ``_interview_support`` so they can also be imported as plain helpers
inside Hypothesis ``@composite`` strategies (which run outside the fixture
scope).

Requirements: 11.1
"""

from __future__ import annotations

import pytest

from tests.modules.recruitment._interview_support import (
    FakeCalendarPort,
    FixedClock,
    SpyAuditSink,
)


@pytest.fixture
def fake_calendar_port() -> FakeCalendarPort:
    """A default :class:`FakeCalendarPort` with no scripted outcomes.

    Records every adapter call and returns synthesized success events; tests
    that need failures or 401-refresh paths construct their own with scripted
    outcome queues instead.
    """
    return FakeCalendarPort()


@pytest.fixture
def spy_audit_sink() -> SpyAuditSink:
    """A :class:`SpyAuditSink` that records audit entries without failing."""
    return SpyAuditSink()


@pytest.fixture
def fixed_clock() -> FixedClock:
    """A deterministic :class:`FixedClock` for the future-``start`` rule (R1.4)."""
    return FixedClock()
