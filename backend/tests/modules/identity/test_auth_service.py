"""Tests for local Identity authentication."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.identity.application.auth_service import AuthService


@pytest.fixture
def service() -> AuthService:
    settings = MagicMock(refresh_token_expire_days=7)
    token_service = MagicMock()
    token_service.create_access_token.return_value = "access"
    token_service.create_refresh_token.return_value = ("refresh", "hash")
    token_service.revoke_user_tokens = AsyncMock()
    user = MagicMock(
        id=uuid4(),
        email="hr@example.com",
        password_hash=None,
        is_active=True,
        employee_id=None,
        must_change_password=False,
    )
    repository = MagicMock()
    repository.get_by_email = AsyncMock(return_value=user)
    repository.get_by_employee_id = AsyncMock(return_value=None)
    repository.create_local_account = AsyncMock(return_value=user)
    repository.update_password = AsyncMock(return_value=user)
    repository.session = MagicMock()
    repository.session.flush = AsyncMock()
    refresh_repository = MagicMock()
    refresh_repository.store = AsyncMock()
    refresh_repository.find_by_token_hash = AsyncMock(return_value=None)
    refresh_repository.revoke = AsyncMock()
    service = AuthService(
        settings=settings,
        token_service=token_service,
        user_repository=repository,
        refresh_token_repository=refresh_repository,
    )
    service._test_user = user
    return service


@pytest.mark.asyncio
async def test_login_uses_local_password(service: AuthService) -> None:
    service._test_user.password_hash = "not-a-real-hash"
    from src.modules.identity.application import auth_service as module

    module.verify_password = lambda password, password_hash: password == "secret"
    result = await service.login("hr@example.com", "secret")

    assert result.access_token == "access"
    service._token_service.revoke_user_tokens.assert_awaited_once_with(service._test_user.id)


@pytest.mark.asyncio
async def test_logout_revokes_local_refresh_token(service: AuthService) -> None:
    record = MagicMock()
    service._refresh_token_repository.find_by_token_hash = AsyncMock(return_value=record)

    await service.logout("refresh")

    service._refresh_token_repository.revoke.assert_awaited_once()
