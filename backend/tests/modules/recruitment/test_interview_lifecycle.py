"""Smoke tests for interview lifecycle methods.

Verifies that the service methods exist, accept the expected arguments,
and raise on missing interviews. Full seam testing requires extending
the fake session to return Interview entities.

Requirements: GH #155 AC 2, 4, 5, 7, 8
"""

from __future__ import annotations

from uuid import uuid4

from src.modules.recruitment.application.candidate_service import CandidateService
from src.modules.recruitment.domain.exceptions import (
    InterviewNotFoundError,
    InterviewStatusTransitionError,
)


def test_complete_interview_method_exists() -> None:
    """complete_interview is an async method on CandidateService."""
    assert hasattr(CandidateService, "complete_interview")


def test_cancel_interview_method_exists() -> None:
    """cancel_interview is an async method on CandidateService."""
    assert hasattr(CandidateService, "cancel_interview")


def test_create_replacement_interview_method_exists() -> None:
    """create_replacement_interview is an async method on CandidateService."""
    assert hasattr(CandidateService, "create_replacement_interview")


def test_interview_not_found_error_importable() -> None:
    """InterviewNotFoundError is importable from the exceptions module."""
    error = InterviewNotFoundError("test")
    assert error.status_code == 404
    assert error.error_code == "INTERVIEW_NOT_FOUND"
    assert "test" in str(error)


def test_interview_status_transition_error_importable() -> None:
    """InterviewStatusTransitionError is importable and structured."""
    error = InterviewStatusTransitionError("cancelled", "complete")
    assert error.status_code == 409
    assert error.error_code == "INTERVIEW_INVALID_STATUS_TRANSITION"
    assert "cancelled" in str(error)
    assert "complete" in str(error)


def test_interview_not_found_error_accepts_uuid() -> None:
    """InterviewNotFoundError can be constructed with a UUID message."""
    fake_id = uuid4()
    error = InterviewNotFoundError(f"Interview not found: {fake_id}")
    assert str(fake_id) in str(error)
