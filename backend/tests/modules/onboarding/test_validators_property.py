"""Property-based tests for the onboarding event payload validator.

Feature: onboarding, Property 5: Invalid or malformed events are rejected
without side effects

These tests exercise ``validate_event_payload`` (the shared validation helper
the ARQ consumer runs before touching the creation path) against malformed
``candidate_accepted`` event payloads: payloads missing one or more required
fields, payloads whose ``candidate_id`` is empty or whitespace, and payloads
whose ``email`` has an invalid shape. The validator must reject every such
payload by raising :class:`InvalidEventPayloadError`, and the guarded creation
path (modelled here by a spy service) must never be invoked.

Validates: Requirements 1.6, 2.6
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from unittest.mock import Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.onboarding.application.validators import (
    EMAIL_MAX_LENGTH,
    validate_event_payload,
)
from src.modules.onboarding.domain.exceptions import InvalidEventPayloadError

# Printable ASCII excluding the space and the '@' character, used to build
# field values that are well-formed except where a category deliberately
# injects an invalidity.
_SAFE_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="@")
_REQUIRED_FIELDS = ("candidate_id", "name", "email")


def _validate_then_create(payload: Mapping[str, Any], service: Mock) -> None:
    """Validate a payload and only then invoke the creation path.

    Mirrors the consumer guard: ``service.start_from_event`` is reachable only
    when validation succeeds. For an invalid payload ``validate_event_payload``
    raises first, so the spy is never touched — proving "no side effects".
    """
    validated = validate_event_payload(payload)
    service.start_from_event(
        candidate_id=validated.candidate_id,
        full_name=validated.full_name,
        email=validated.email,
        event_id="evt-test",
    )


def _valid_names() -> st.SearchStrategy[str]:
    """Names that are valid after trimming (1-255 non-whitespace characters)."""
    return st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=255)


@st.composite
def _valid_emails(draw: st.DrawFn) -> str:
    """Syntactically valid emails: one '@', non-empty local and domain, <=320."""
    local = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    domain = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=64))
    return f"{local}@{domain}"


@st.composite
def _missing_key_payloads(draw: st.DrawFn) -> dict[str, Any]:
    """Payloads omitting at least one required logical field.

    Starts from an all-valid payload and drops a non-empty subset of the
    required fields. Dropping ``name`` removes the only name-bearing key, so the
    name maps to nothing (the validator also accepts ``full_name``, which is
    never added here).
    """
    payload: dict[str, Any] = {
        "candidate_id": draw(st.uuids()),
        "name": draw(_valid_names()),
        "email": draw(_valid_emails()),
    }
    to_omit = draw(st.lists(st.sampled_from(_REQUIRED_FIELDS), min_size=1, max_size=3, unique=True))
    for key in to_omit:
        payload.pop(key, None)
    return payload


@st.composite
def _empty_candidate_id_payloads(draw: st.DrawFn) -> dict[str, Any]:
    """Payloads whose ``candidate_id`` is empty or whitespace-only."""
    blank = draw(st.text(alphabet=" \t\r\n", min_size=0, max_size=5))
    return {
        "candidate_id": blank,
        "name": draw(_valid_names()),
        "email": draw(_valid_emails()),
    }


@st.composite
def _invalid_email_payloads(draw: st.DrawFn) -> dict[str, Any]:
    """Payloads with a structurally invalid ``email`` (others valid)."""
    no_at = st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=40)
    empty_local = st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=40).map(lambda d: f"@{d}")
    empty_domain = st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=40).map(
        lambda local: f"{local}@"
    )
    multiple_at = st.lists(
        st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=20),
        min_size=3,
        max_size=4,
    ).map(lambda parts: "@".join(parts))
    too_long = st.integers(min_value=EMAIL_MAX_LENGTH + 1, max_value=EMAIL_MAX_LENGTH + 50).map(
        lambda total: f"{'a' * (total - 2)}@b"
    )
    email = draw(st.one_of(no_at, empty_local, empty_domain, multiple_at, too_long))
    return {
        "candidate_id": draw(st.uuids()),
        "name": draw(_valid_names()),
        "email": email,
    }


def _invalid_payloads() -> st.SearchStrategy[dict[str, Any]]:
    """Union of every malformed-payload category for this property."""
    return st.one_of(
        _missing_key_payloads(),
        _empty_candidate_id_payloads(),
        _invalid_email_payloads(),
    )


# Feature: onboarding, Property 5: Invalid or malformed events are rejected
# without side effects
@settings(max_examples=200)
@given(payload=_invalid_payloads())
def test_event_validation_rejects_malformed_events_without_side_effects(
    payload: dict[str, Any],
) -> None:
    """Malformed events raise and never reach the creation path.

    Validates: Requirements 1.6, 2.6
    """
    service_spy = Mock()

    with pytest.raises(InvalidEventPayloadError):
        _validate_then_create(payload, service_spy)

    # No service creation path is invoked for a rejected event.
    service_spy.start_from_event.assert_not_called()
    assert service_spy.mock_calls == []
