"""Tests for SetupService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.identity.application.password_service import PasswordService
from src.modules.identity.domain.entities import UserRole
from src.modules.setup.application.setup_service import (
    SetupAlreadyCompleteError,
    SetupService,
)


def _result(value: object | None) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.first.return_value = value
    return result


@pytest.mark.asyncio
async def test_get_status_reports_empty_setup() -> None:
    session = MagicMock()
    session.execute = AsyncMock(side_effect=[_result(None), _result(None)])
    service = SetupService(session)

    status = await service.get_status()

    assert status == {
        "setup_complete": False,
        "admin_exists": False,
        "org_configured": False,
        "ai_provider_configured": False,
    }


@pytest.mark.asyncio
async def test_create_first_admin_hashes_password_and_sets_role() -> None:
    session = MagicMock()
    session.execute = AsyncMock(side_effect=[_result(None), _result(None), _result(None)])
    session.add = MagicMock()
    session.flush = AsyncMock()
    service = SetupService(session)

    user = await service.create_first_admin("admin@hrspace.local", "password123", "Admin")

    assert user.email == "admin@hrspace.local"
    assert user.role == UserRole.SUPER_ADMIN
    assert user.google_sub.startswith("setup:")
    assert PasswordService.verify_password("password123", user.password_hash)
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_setup_requires_admin() -> None:
    session = MagicMock()
    session.execute = AsyncMock(side_effect=[_result(None), _result(None)])
    session.add = MagicMock()
    session.flush = AsyncMock()
    service = SetupService(session)

    with pytest.raises(SetupAlreadyCompleteError):
        await service.complete_setup()
