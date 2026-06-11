"""Property-based tests for attachment validation logic.

These tests exercise ``validate_attachment`` against various combinations of
MIME types and file sizes to ensure the invariants hold true across a wide range
of generated inputs.
"""

from hypothesis import given
from hypothesis import strategies as st

from src.modules.recruitment.application.validators import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    validate_attachment,
)

# Strategy for valid MIME types
_valid_mime_types = st.sampled_from(list(ALLOWED_MIME_TYPES))

# Strategy for invalid MIME types (any text that isn't in the allowed set)
_invalid_mime_types = st.text().filter(lambda mime: mime not in ALLOWED_MIME_TYPES)

# Strategy for valid file sizes (0 to MAX_FILE_SIZE_BYTES)
_valid_sizes = st.integers(min_value=0, max_value=MAX_FILE_SIZE_BYTES)

# Strategy for invalid file sizes (strictly greater than MAX_FILE_SIZE_BYTES)
# Capping at a reasonable upper bound for generation, e.g., 100GB
_invalid_sizes = st.integers(min_value=MAX_FILE_SIZE_BYTES + 1, max_value=100 * 1024 * 1024 * 1024)


@given(mime_type=_valid_mime_types, size_bytes=_valid_sizes)
def test_valid_attachment_is_accepted(mime_type: str, size_bytes: int) -> None:
    """An attachment with an allowed MIME type and size within limits is accepted."""
    result = validate_attachment(mime_type, size_bytes)
    assert result.is_valid is True
    assert result.error_message is None


@given(mime_type=_invalid_mime_types, size_bytes=_valid_sizes)
def test_invalid_mime_type_is_rejected(mime_type: str, size_bytes: int) -> None:
    """An attachment with an invalid MIME type is rejected, even if size is valid."""
    result = validate_attachment(mime_type, size_bytes)
    assert result.is_valid is False
    assert result.error_message is not None
    assert "MIME type" in result.error_message
    assert "not allowed" in result.error_message


@given(mime_type=_valid_mime_types, size_bytes=_invalid_sizes)
def test_oversized_attachment_is_rejected(mime_type: str, size_bytes: int) -> None:
    """An attachment exceeding the size limit is rejected, even if MIME type is valid."""
    result = validate_attachment(mime_type, size_bytes)
    assert result.is_valid is False
    assert result.error_message is not None
    assert "File size" in result.error_message
    assert "exceeds" in result.error_message


@given(mime_type=_invalid_mime_types, size_bytes=_invalid_sizes)
def test_invalid_mime_type_and_oversized_reports_mime_error_first(
    mime_type: str, size_bytes: int
) -> None:
    """When both MIME type and size are invalid, the MIME type error takes precedence."""
    result = validate_attachment(mime_type, size_bytes)
    assert result.is_valid is False
    assert result.error_message is not None
    assert "MIME type" in result.error_message


@given(
    mime_type=_valid_mime_types,
    size_bytes=st.integers(min_value=0),
    max_size=st.integers(min_value=0, max_value=100 * 1024 * 1024 * 1024),
)
def test_custom_max_size_is_respected(mime_type: str, size_bytes: int, max_size: int) -> None:
    """The custom max_file_size_bytes parameter correctly overrides the default limit."""
    result = validate_attachment(mime_type, size_bytes, max_file_size_bytes=max_size)
    if size_bytes <= max_size:
        assert result.is_valid is True
        assert result.error_message is None
    else:
        assert result.is_valid is False
        assert result.error_message is not None
        assert "File size" in result.error_message
