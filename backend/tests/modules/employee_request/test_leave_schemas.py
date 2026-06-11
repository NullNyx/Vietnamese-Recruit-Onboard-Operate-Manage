"""Tests for Leave request schema validation."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from src.modules.employee_request.api.schemas import LeaveCreateRequest


class TestLeaveCreateRequest:
    """Tests for LeaveCreateRequest schema validation."""

    def test_valid_request(self):
        body = LeaveCreateRequest(
            leave_type="annual",
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 17),
            reason="Vacation",
        )
        assert body.leave_type == "annual"
        assert body.start_date == date(2026, 6, 15)
        assert body.end_date == date(2026, 6, 17)
        assert body.reason == "Vacation"

    def test_single_day_valid(self):
        body = LeaveCreateRequest(
            leave_type="sick",
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 15),
            reason="Sick day",
        )
        assert body.start_date == body.end_date

    def test_rejects_end_before_start(self):
        with pytest.raises(ValidationError):
            LeaveCreateRequest(
                leave_type="annual",
                start_date=date(2026, 6, 17),
                end_date=date(2026, 6, 15),
                reason="Invalid",
            )

    def test_rejects_invalid_leave_type(self):
        with pytest.raises(ValidationError):
            LeaveCreateRequest(
                leave_type="maternity",
                start_date=date(2026, 6, 15),
                end_date=date(2026, 6, 17),
                reason="Maternity leave",
            )

    def test_rejects_empty_reason(self):
        with pytest.raises(ValidationError):
            LeaveCreateRequest(
                leave_type="annual",
                start_date=date(2026, 6, 15),
                end_date=date(2026, 6, 17),
                reason="",
            )

    def test_rejects_whitespace_reason(self):
        with pytest.raises(ValidationError):
            LeaveCreateRequest(
                leave_type="annual",
                start_date=date(2026, 6, 15),
                end_date=date(2026, 6, 17),
                reason="   ",
            )

    def test_accepts_all_valid_types(self):
        for lt in ["annual", "sick", "unpaid", "other"]:
            body = LeaveCreateRequest(
                leave_type=lt,
                start_date=date(2026, 6, 15),
                end_date=date(2026, 6, 17),
                reason=f"Leave type {lt}",
            )
            assert body.leave_type == lt
