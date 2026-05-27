"""Unit tests for the sensitive field masking utility."""

import pytest

from src.modules.self_service.application.masking import mask_sensitive_field


class TestMaskSensitiveField:
    """Tests for mask_sensitive_field function."""

    def test_none_input_returns_none(self) -> None:
        assert mask_sensitive_field(None) is None

    def test_empty_string_returns_empty(self) -> None:
        assert mask_sensitive_field("") == ""

    def test_single_char_masked_entirely(self) -> None:
        assert mask_sensitive_field("a") == "*"

    def test_two_chars_masked_entirely(self) -> None:
        assert mask_sensitive_field("ab") == "**"

    def test_three_chars_masked_entirely(self) -> None:
        assert mask_sensitive_field("abc") == "***"

    def test_four_chars_preserves_all(self) -> None:
        # N=4, N-4=0, so no masking prefix, all 4 chars preserved
        assert mask_sensitive_field("1234") == "1234"

    def test_five_chars_masks_first_one(self) -> None:
        assert mask_sensitive_field("12345") == "*2345"

    def test_twelve_char_id_number(self) -> None:
        assert mask_sensitive_field("123456789012") == "********9012"

    def test_ten_char_tax_code(self) -> None:
        assert mask_sensitive_field("0123456789") == "******6789"

    def test_preserves_last_four_characters_exactly(self) -> None:
        result = mask_sensitive_field("ABCDEFGH")
        assert result[-4:] == "EFGH"
        assert result[:-4] == "****"

    def test_masking_prefix_is_all_asterisks(self) -> None:
        result = mask_sensitive_field("1234567890")
        prefix = result[:-4]
        assert all(c == "*" for c in prefix)
        assert len(prefix) == 6

    def test_result_length_matches_input_length(self) -> None:
        for value in ["a", "ab", "abc", "abcd", "abcde", "123456789012"]:
            result = mask_sensitive_field(value)
            assert result is not None
            assert len(result) == len(value)
