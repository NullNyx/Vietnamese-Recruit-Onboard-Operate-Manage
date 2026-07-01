"""Tests for PasswordService."""

from src.modules.identity.application.password_service import PasswordService


def test_hash_password_round_trip() -> None:
    encoded = PasswordService.hash_password("correct horse battery staple")

    assert PasswordService.verify_password("correct horse battery staple", encoded)
    assert not PasswordService.verify_password("wrong password", encoded)


def test_verify_password_rejects_malformed_hash() -> None:
    assert not PasswordService.verify_password("pw", "bad")
    assert not PasswordService.verify_password("pw", "salt$not-an-int$hash")
