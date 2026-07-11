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
    FULL_NAME_MAX_LENGTH,
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

    # Occasionally, instead of omitting a key, set it to None, which hits the `is None`
    # branches specifically. `payload.get("key")` is None both if omitted and if value is None.
    # To be perfectly sure we cover `value is None` explicitly if it wasn't hit, we can
    # randomly add a None key back.
    if draw(st.booleans()) and to_omit:
        key_to_none = draw(st.sampled_from(to_omit))
        payload[key_to_none] = None

    return payload


@st.composite
def _none_email_payloads(draw: st.DrawFn) -> dict[str, Any]:
    """Payloads where email is explicitly None."""
    return {
        "candidate_id": draw(st.uuids()),
        "name": draw(_valid_names()),
        "email": None,
    }


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
def _invalid_candidate_id_type_payloads(draw: st.DrawFn) -> dict[str, Any]:
    invalid_type = draw(st.integers() | st.floats() | st.booleans() | st.lists(st.integers()))
    return {
        "candidate_id": invalid_type,
        "name": draw(_valid_names()),
        "email": draw(_valid_emails()),
    }


@st.composite
def _invalid_candidate_id_string_payloads(draw: st.DrawFn) -> dict[str, Any]:
    # We want to ensure it's not empty, otherwise it hits empty-validation.
    invalid_string = draw(st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=10))
    return {
        "candidate_id": invalid_string,
        "name": draw(_valid_names()),
        "email": draw(_valid_emails()),
    }


@st.composite
def _invalid_name_type_payloads(draw: st.DrawFn) -> dict[str, Any]:
    invalid_type = draw(st.integers() | st.floats() | st.booleans() | st.lists(st.integers()))
    key = draw(st.sampled_from(["name", "full_name"]))
    return {
        "candidate_id": draw(st.uuids()),
        key: invalid_type,
        "email": draw(_valid_emails()),
    }


@st.composite
def _empty_name_payloads(draw: st.DrawFn) -> dict[str, Any]:
    empty_or_whitespace = draw(st.text(alphabet=" \t\r\n", min_size=0, max_size=5))
    key = draw(st.sampled_from(["name", "full_name"]))
    return {
        "candidate_id": draw(st.uuids()),
        key: empty_or_whitespace,
        "email": draw(_valid_emails()),
    }


@st.composite
def _too_long_name_payloads(draw: st.DrawFn) -> dict[str, Any]:
    too_long = draw(
        st.text(
            alphabet=_SAFE_ALPHABET,
            min_size=FULL_NAME_MAX_LENGTH + 1,
            max_size=FULL_NAME_MAX_LENGTH + 50,
        )
    )
    key = draw(st.sampled_from(["name", "full_name"]))
    return {
        "candidate_id": draw(st.uuids()),
        key: too_long,
        "email": draw(_valid_emails()),
    }


@st.composite
def _invalid_email_type_payloads(draw: st.DrawFn) -> dict[str, Any]:
    invalid_type = draw(st.integers() | st.floats() | st.booleans() | st.lists(st.integers()))
    return {
        "candidate_id": draw(st.uuids()),
        "name": draw(_valid_names()),
        "email": invalid_type,
    }


@st.composite
def _empty_email_payloads(draw: st.DrawFn) -> dict[str, Any]:
    empty_or_whitespace = draw(st.text(alphabet=" \t\r\n", min_size=0, max_size=5))
    return {
        "candidate_id": draw(st.uuids()),
        "name": draw(_valid_names()),
        "email": empty_or_whitespace,
    }


@st.composite
def _too_long_email_payloads(draw: st.DrawFn) -> dict[str, Any]:
    total_length = draw(
        st.integers(min_value=EMAIL_MAX_LENGTH + 1, max_value=EMAIL_MAX_LENGTH + 50)
    )
    too_long = f"{'a' * (total_length - 2)}@b"
    return {
        "candidate_id": draw(st.uuids()),
        "name": draw(_valid_names()),
        "email": too_long,
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

    email = draw(st.one_of(no_at, empty_local, empty_domain, multiple_at))
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
        _invalid_candidate_id_type_payloads(),
        _invalid_candidate_id_string_payloads(),
        _invalid_name_type_payloads(),
        _empty_name_payloads(),
        _too_long_name_payloads(),
        _invalid_email_type_payloads(),
        _empty_email_payloads(),
        _too_long_email_payloads(),
        _invalid_email_payloads(),
        _none_email_payloads(),
    )


@st.composite
def _valid_payloads(draw: st.DrawFn) -> dict[str, Any]:
    """Well-formed payloads representing a successful parsing path."""
    # Randomly choose between "name" and "full_name" to exercise line 77
    key = draw(st.sampled_from(["name", "full_name"]))

    payload = {
        "event_type": "candidate_accepted",
        "candidate_id": draw(st.uuids()),
        key: draw(_valid_names()),
        "email": draw(_valid_emails()),
    }

    # Optionally add extra keys to simulate raw events with extra data.
    # Exclude required keys to avoid overwriting them with invalid values.
    extra_keys_strategy = st.text(min_size=1).filter(
        lambda x: x not in ("event_type", "candidate_id", "name", "full_name", "email")
    )
    extra_keys = draw(st.dictionaries(keys=extra_keys_strategy, values=st.integers(), max_size=3))
    payload.update(extra_keys)

    return payload


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


@settings(max_examples=200)
@given(payload=_valid_payloads())
def test_event_validation_accepts_valid_events(payload: dict[str, Any]) -> None:
    """Valid events are successfully parsed and cleanly extracted.

    Validates: Successful paths for valid data extraction.
    """
    validated = validate_event_payload(payload)

    # UUID should match exactly if it was generated as UUID
    # or match the parsed UUID if passed as string (though _valid_payloads uses uuids())
    expected_id = payload["candidate_id"]
    if isinstance(expected_id, str):
        import uuid

        expected_id = uuid.UUID(expected_id.strip())
    assert validated.candidate_id == expected_id

    # Name should match the expected 'name' or 'full_name' field
    expected_name = payload.get("name")
    if expected_name is None:
        expected_name = payload.get("full_name")
    assert validated.full_name == expected_name.strip()

    # Email should match exactly
    assert validated.email == payload["email"].strip()
