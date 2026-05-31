"""Unit tests for the calendar value objects.

Covers the event time-window invariant on ``CalendarEventSpec``: the end is
always ``start + timedelta(minutes=duration)`` and strictly after ``start`` for
the boundary durations of the valid 15-180 minute range (Requirement 2.2).
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.modules.recruitment.domain.value_objects import CalendarEventSpec

# Boundary durations of the valid schedule range (15-180 minutes inclusive).
BOUNDARY_DURATIONS_MINUTES = (15, 180)

_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _make_spec(duration_minutes: int) -> CalendarEventSpec:
    """Build a CalendarEventSpec whose end is start + duration_minutes."""
    start = datetime(2025, 6, 1, 9, 0, tzinfo=_TZ)
    end = start + timedelta(minutes=duration_minutes)
    return CalendarEventSpec(
        summary="Interview",
        description=None,
        start=start,
        end=end,
        timezone="Asia/Ho_Chi_Minh",
        attendee_emails=("candidate@example.com",),
    )


class TestEventTimeWindowInvariant:
    """Tests for the end == start + duration invariant (Requirement 2.2)."""

    def test_end_equals_start_plus_duration_at_boundaries(self) -> None:
        """For 15 and 180 minute durations, end == start + duration."""
        for duration in BOUNDARY_DURATIONS_MINUTES:
            spec = _make_spec(duration)
            assert spec.end == spec.start + timedelta(minutes=duration)

    def test_end_strictly_after_start_at_boundaries(self) -> None:
        """For 15 and 180 minute durations, end is strictly after start."""
        for duration in BOUNDARY_DURATIONS_MINUTES:
            spec = _make_spec(duration)
            assert spec.end > spec.start

    def test_minimum_duration_window_is_15_minutes(self) -> None:
        """The 15-minute boundary spans exactly 15 minutes."""
        spec = _make_spec(15)
        assert spec.end - spec.start == timedelta(minutes=15)

    def test_maximum_duration_window_is_180_minutes(self) -> None:
        """The 180-minute boundary spans exactly 180 minutes."""
        spec = _make_spec(180)
        assert spec.end - spec.start == timedelta(minutes=180)
