"""Tests for identity domain entities."""

from src.modules.identity.domain.entities import User, UserRole


def test_user_role_includes_new_names_and_backward_compatible_aliases() -> None:
    assert UserRole.SUPER_ADMIN.value == "super_admin"
    assert UserRole.HR_ADMIN.value == "admin"
    assert UserRole.HR_STAFF.value == "user"
    assert UserRole.READ_ONLY.value == "read_only"
    assert UserRole.ADMIN is UserRole.HR_ADMIN
    assert UserRole.USER is UserRole.HR_STAFF


def test_user_has_password_hash_field() -> None:
    assert "password_hash" in User.model_fields
    assert User.model_fields["password_hash"].default is None
