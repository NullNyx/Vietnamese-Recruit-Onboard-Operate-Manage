"""Unit tests for onboarding validation logic."""

from uuid import uuid4

import pytest

from src.modules.onboarding.application.validators import _validate_candidate_id
from src.modules.onboarding.domain.exceptions import InvalidEventPayloadError


class TestValidateCandidateId:
    """Tests for _validate_candidate_id function."""

    def test_missing_value_raises_error(self):
        """A missing (None) candidate_id raises InvalidEventPayloadError."""
        with pytest.raises(
            InvalidEventPayloadError, match="Event payload is missing 'candidate_id'"
        ):
            _validate_candidate_id(None)

    def test_valid_uuid_object_returns_same_object(self):
        """A valid UUID object is returned unmodified."""
        candidate_uuid = uuid4()
        result = _validate_candidate_id(candidate_uuid)
        assert result == candidate_uuid

    def test_valid_uuid_string_returns_uuid_object(self):
        """A valid UUID string is parsed and returned as a UUID object."""
        candidate_uuid = uuid4()
        result = _validate_candidate_id(str(candidate_uuid))
        assert result == candidate_uuid

    def test_valid_uuid_string_with_whitespace_is_trimmed(self):
        """A valid UUID string with surrounding whitespace is parsed and returned."""
        candidate_uuid = uuid4()
        result = _validate_candidate_id(f"  {candidate_uuid}  ")
        assert result == candidate_uuid

    def test_empty_string_raises_error(self):
        """An empty or whitespace-only string raises InvalidEventPayloadError."""
        with pytest.raises(
            InvalidEventPayloadError, match="Event payload 'candidate_id' must not be empty"
        ):
            _validate_candidate_id("   ")

    def test_invalid_uuid_string_raises_error(self):
        """A string that is not a valid UUID raises InvalidEventPayloadError."""
        with pytest.raises(
            InvalidEventPayloadError, match="Event payload 'candidate_id' is not a valid UUID"
        ):
            _validate_candidate_id("not-a-uuid")

    def test_unexpected_type_raises_error(self):
        """An unexpected type (e.g. an integer) raises InvalidEventPayloadError."""
        with pytest.raises(
            InvalidEventPayloadError,
            match="Event payload 'candidate_id' must be a string or UUID, got int",
        ):
            _validate_candidate_id(123)
