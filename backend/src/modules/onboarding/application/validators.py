"""Shared validation helpers for the Onboarding module.

Centralizes validation of the ``candidate_accepted`` event payload so the ARQ
consumer and any future caller share a single definition of the rules.

The email and name rules mirror the recruitment module's
``validate_candidate_fields`` (an email must contain exactly one ``@`` with a
non-empty local part and a non-empty domain part), extended here to the
``Employee`` field bounds: ``full_name`` must be 1-255 characters and ``email``
must be 1-320 characters. ``candidate_id`` must be present and resolve to a
valid UUID.

Any violation raises :class:`InvalidEventPayloadError`; on success the cleaned
and parsed values are returned (``candidate_id`` as a :class:`~uuid.UUID`,
``full_name`` and ``email`` as trimmed strings).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final
from uuid import UUID

from src.modules.onboarding.domain.exceptions import InvalidEventPayloadError

# Employee field bounds (see requirements 2.2 / 2.6).
FULL_NAME_MAX_LENGTH: Final[int] = 255
EMAIL_MAX_LENGTH: Final[int] = 320

# Email rule mirrored from recruitment.validate_candidate_fields: exactly one
# '@' separating a non-empty local part from a non-empty domain part.
_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[^@]+@[^@]+$")


@dataclass(frozen=True, slots=True)
class ValidatedEventPayload:
    """The cleaned, validated fields of a ``candidate_accepted`` event.

    Attributes:
        candidate_id: The originating candidate identifier, parsed to a UUID.
        full_name: The trimmed candidate name, mapped to the Employee
            ``full_name`` (1-255 characters).
        email: The trimmed, syntactically valid email (1-320 characters).
    """

    candidate_id: UUID
    full_name: str
    email: str


def validate_event_payload(payload: Mapping[str, Any]) -> ValidatedEventPayload:
    """Validate a ``candidate_accepted`` event payload and return cleaned fields.

    The event payload carries ``candidate_id``, ``name`` (mapped to the Employee
    ``full_name``), and ``email``. Each field is validated against the rules
    described in the module docstring.

    Args:
        payload: The raw event payload mapping (e.g. an ARQ job argument).

    Returns:
        A :class:`ValidatedEventPayload` holding the parsed ``candidate_id``
        and the trimmed ``full_name`` and ``email``.

    Raises:
        InvalidEventPayloadError: If any required field is missing, empty, of an
            unexpected type, out of bounds, or (for ``email``) not syntactically
            valid.
    """
    candidate_id = _validate_candidate_id(payload.get("candidate_id"))
    # The recruitment event uses the key ``name``; accept ``full_name`` too so a
    # future caller passing the Employee field name directly is also supported.
    raw_name = payload.get("name")
    if raw_name is None:
        raw_name = payload.get("full_name")
    full_name = _validate_full_name(raw_name)
    email = _validate_email(payload.get("email"))
    return ValidatedEventPayload(candidate_id=candidate_id, full_name=full_name, email=email)


def _validate_candidate_id(value: Any) -> UUID:
    """Validate and parse the ``candidate_id`` field to a UUID."""
    if value is None:
        raise InvalidEventPayloadError("Event payload is missing 'candidate_id'")
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise InvalidEventPayloadError("Event payload 'candidate_id' must not be empty")
        try:
            return UUID(text)
        except ValueError as exc:
            raise InvalidEventPayloadError(
                f"Event payload 'candidate_id' is not a valid UUID: {value!r}"
            ) from exc
    raise InvalidEventPayloadError(
        f"Event payload 'candidate_id' must be a string or UUID, got {type(value).__name__}"
    )


def _validate_full_name(value: Any) -> str:
    """Validate the ``full_name`` field against the Employee bounds (1-255)."""
    if value is None:
        raise InvalidEventPayloadError("Event payload is missing 'full_name'")
    if not isinstance(value, str):
        raise InvalidEventPayloadError(
            f"Event payload 'full_name' must be a string, got {type(value).__name__}"
        )
    full_name = value.strip()
    if not full_name:
        raise InvalidEventPayloadError("Event payload 'full_name' must not be empty")
    if len(full_name) > FULL_NAME_MAX_LENGTH:
        raise InvalidEventPayloadError(
            f"Event payload 'full_name' must not exceed {FULL_NAME_MAX_LENGTH} characters"
        )
    return full_name


def _validate_email(value: Any) -> str:
    """Validate the ``email`` field: 1-320 chars and syntactically valid."""
    if value is None:
        raise InvalidEventPayloadError("Event payload is missing 'email'")
    if not isinstance(value, str):
        raise InvalidEventPayloadError(
            f"Event payload 'email' must be a string, got {type(value).__name__}"
        )
    email = value.strip()
    if not email:
        raise InvalidEventPayloadError("Event payload 'email' must not be empty")
    if len(email) > EMAIL_MAX_LENGTH:
        raise InvalidEventPayloadError(
            f"Event payload 'email' must not exceed {EMAIL_MAX_LENGTH} characters"
        )
    if not _EMAIL_PATTERN.match(email):
        raise InvalidEventPayloadError(
            "Event payload 'email' must contain exactly one '@' with non-empty "
            "local and domain parts"
        )
    return email
