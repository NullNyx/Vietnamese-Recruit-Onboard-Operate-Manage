"""Tests for Overtime API schema validation."""

from __future__ import annotations

from datetime import date, time

import pytest
from pydantic import ValidationError

from src.modules.employee_request.api.schemas import OvertimeCreateRequest


class TestOvertimeCreateRequest:
    """Tests for OvertimeCreateRequest schema validation."""

    def test_valid_request(self):
        """Valid overtime request passes schema validation."""
        body = OvertimeCreateRequest(
            work_date=date(2026, 6, 11),
            start_time=time(18, 0),
            end_time=time(20, 30),
            reason="Project deadline",
        )
        assert body.work_date == date(2026, 6, 11)
        assert body.start_time == time(18, 0)
        assert body.end_time == time(20, 30)
        assert body.reason == "Project deadline"
        assert body.project_or_task is None

    def test_valid_with_project(self):
        """Optional project_or_task is accepted."""
        body = OvertimeCreateRequest(
            work_date=date(2026, 6, 11),
            start_time=time(18, 0),
            end_time=time(20, 30),
            reason="Feature work",
            project_or_task="VROOM-123",
        )
        assert body.project_or_task == "VROOM-123"

    def test_rejects_empty_reason(self):
        """Empty reason is rejected."""
        with pytest.raises(ValidationError):
            OvertimeCreateRequest(
                work_date=date(2026, 6, 11),
                start_time=time(18, 0),
                end_time=time(20, 30),
                reason="",
            )

    def test_rejects_whitespace_only_reason(self):
        """Whitespace-only reason is rejected."""
        with pytest.raises(ValidationError):
            OvertimeCreateRequest(
                work_date=date(2026, 6, 11),
                start_time=time(18, 0),
                end_time=time(20, 30),
                reason="   ",
            )
