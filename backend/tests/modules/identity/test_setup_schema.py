"""Tests for First-Run Setup request validation."""

import pytest
from pydantic import ValidationError

from src.modules.identity.api.schemas import FirstRunSetupRequest


def test_normalizes_setup_identity_fields() -> None:
    request = FirstRunSetupRequest(
        organization_name="  Acme Vietnam  ",
        name="  HR Admin  ",
        email=" HR@Example.COM ",
        password="a" * 12,
        password_confirmation="a" * 12,
    )

    assert request.organization_name == "Acme Vietnam"
    assert request.name == "HR Admin"
    assert request.email == "hr@example.com"


@pytest.mark.parametrize(
    "password,password_confirmation",
    [("a" * 11, "a" * 11), ("a" * 12, "b" * 12)],
)
def test_rejects_short_or_mismatched_passwords(password: str, password_confirmation: str) -> None:
    with pytest.raises(ValidationError):
        FirstRunSetupRequest(
            organization_name="Acme",
            name="HR Admin",
            email="hr@example.com",
            password=password,
            password_confirmation=password_confirmation,
        )
