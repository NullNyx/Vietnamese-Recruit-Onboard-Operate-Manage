"""Candidate validation utilities for the Recruitment module.

Provides the candidate status state machine (``VALID_TRANSITIONS``),
transition validation, and CV field validation — pure functions shared
by CandidateService and any future services.
"""

from __future__ import annotations

import re
from typing import Any

from src.modules.recruitment.domain.enums import CandidateStatus
from src.modules.recruitment.domain.exceptions import InvalidStatusTransitionError
from src.modules.recruitment.domain.value_objects import ParsedCV

# ─── State Machine Definition ──────────────────────────────────────────

VALID_TRANSITIONS: dict[str, set[str]] = {
    CandidateStatus.NEW: {
        CandidateStatus.REVIEWING,
        CandidateStatus.INTERVIEW_SCHEDULED,
        CandidateStatus.REJECTED,
        CandidateStatus.ARCHIVED,
    },
    CandidateStatus.REVIEWING: {
        CandidateStatus.INTERVIEW_SCHEDULED,
        CandidateStatus.ACCEPTED,
        CandidateStatus.REJECTED,
        CandidateStatus.ARCHIVED,
    },
    CandidateStatus.INTERVIEW_SCHEDULED: {
        CandidateStatus.ACCEPTED,
        CandidateStatus.REJECTED,
        CandidateStatus.ARCHIVED,
    },
    CandidateStatus.ACCEPTED: set(),
    CandidateStatus.REJECTED: set(),
    CandidateStatus.ARCHIVED: set(),
}


# ─── Validation ────────────────────────────────────────────────────────

# Basic email regex: must contain exactly one @ with non-empty local and domain parts
_EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+$")


class CandidateValidationError(Exception):
    """Raised when candidate field validation fails.

    Attributes:
        errors: List of validation error dicts with field and reason.
    """

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        super().__init__(f"Candidate validation failed: {errors}")


def validate_candidate_fields(parsed_cv: ParsedCV) -> list[dict[str, Any]]:
    """Validate required candidate fields from parsed CV data.

    Checks:
    - name: non-empty, ≤ 255 characters
    - email: valid format (contains @, non-empty local and domain parts), ≤ 255 chars

    Args:
        parsed_cv: The parsed CV data to validate.

    Returns:
        List of validation error dicts. Empty list means validation passed.
    """
    errors: list[dict[str, Any]] = []

    # Validate name
    name = parsed_cv.name.strip() if parsed_cv.name else ""
    if not name:
        errors.append({"field": "name", "reason": "Name is required and cannot be empty"})
    elif len(name) > 255:
        errors.append({"field": "name", "reason": "Name must not exceed 255 characters"})

    # Validate email
    email = parsed_cv.email.strip() if parsed_cv.email else ""
    if not email:
        errors.append({"field": "email", "reason": "Email is required and cannot be empty"})
    elif len(email) > 255:
        errors.append({"field": "email", "reason": "Email must not exceed 255 characters"})
    elif not _EMAIL_PATTERN.match(email):
        errors.append(
            {
                "field": "email",
                "reason": (
                    "Email must contain exactly one '@' with non-empty local and domain parts"
                ),
            }
        )

    return errors


def validate_transition(current_status: str, target_status: str, action: str) -> None:
    """Validate that a status transition is allowed by the state machine.

    Args:
        current_status: The candidate's current status.
        target_status: The desired target status.
        action: The action name being performed (for error messages).

    Raises:
        InvalidStatusTransitionError: If the transition is not allowed.
    """
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidStatusTransitionError(current_status, action)
