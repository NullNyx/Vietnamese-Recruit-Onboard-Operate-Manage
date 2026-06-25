"""Unit tests for SetupService.

Tests the first-run setup initialization, token generation, and state checks.
"""

from __future__ import annotations

import pytest

from src.modules.identity.application.setup_service import SetupService
from src.modules.identity.domain.entities import SystemSetup


class FakeSetupRepository:
    """Minimal fake repository for SetupService tests."""

    def __init__(self, setup_record: SystemSetup | None = None) -> None:
        self._record = setup_record

    async def get_setup_record(self) -> SystemSetup | None:
        return self._record

    async def upsert_setup_record(self, record: SystemSetup) -> SystemSetup:
        self._record = record
        return record


@pytest.fixture
def empty_repo() -> FakeSetupRepository:
    """Repository returning no setup record."""
    return FakeSetupRepository(setup_record=None)


@pytest.fixture
def completed_repo() -> FakeSetupRepository:
    """Repository returning a completed setup record."""
    from uuid import uuid4
    from datetime import datetime, UTC
    record = SystemSetup(
        id=uuid4(),
        is_setup_completed=True,
        setup_token=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return FakeSetupRepository(setup_record=record)


@pytest.mark.asyncio
async def test_setup_not_completed_when_db_empty(empty_repo: FakeSetupRepository) -> None:
    """When DB has no SystemSetup record, setup is not completed."""
    service = SetupService(setup_repository=empty_repo)
    assert await service.is_setup_completed() is False


@pytest.mark.asyncio
async def test_setup_completed_when_flag_true(completed_repo: FakeSetupRepository) -> None:
    """When DB has SystemSetup with is_setup_completed=True, setup is completed."""
    service = SetupService(setup_repository=completed_repo)
    assert await service.is_setup_completed() is True


@pytest.mark.asyncio
async def test_initialize_setup_token_creates_token(empty_repo: FakeSetupRepository) -> None:
    """Initializing setup token when DB is empty creates a token and returns it."""
    service = SetupService(setup_repository=empty_repo)
    token = await service.initialize_setup_token()
    
    assert token is not None
    assert token.startswith("VROOM-")
    
    record = await empty_repo.get_setup_record()
    assert record is not None
    assert record.setup_token == token


@pytest.mark.asyncio
async def test_initialize_setup_token_reuses_existing(empty_repo: FakeSetupRepository) -> None:
    """If a setup token already exists, it is reused."""
    service = SetupService(setup_repository=empty_repo)
    token1 = await service.initialize_setup_token()
    token2 = await service.initialize_setup_token()
    
    assert token1 == token2


@pytest.mark.asyncio
async def test_verify_setup_token_success(empty_repo: FakeSetupRepository) -> None:
    """Verifying with the correct token succeeds."""
    service = SetupService(setup_repository=empty_repo)
    token = await service.initialize_setup_token()
    
    is_valid = await service.verify_setup_token(token)
    assert is_valid is True


@pytest.mark.asyncio
async def test_verify_setup_token_failure(empty_repo: FakeSetupRepository) -> None:
    """Verifying with an incorrect token fails."""
    service = SetupService(setup_repository=empty_repo)
    await service.initialize_setup_token()
    
    is_valid = await service.verify_setup_token("WRONG-TOKEN")
    assert is_valid is False


@pytest.mark.asyncio
async def test_lock_setup_success(empty_repo: FakeSetupRepository) -> None:
    """Locking setup sets is_setup_completed to True and clears the token."""
    service = SetupService(setup_repository=empty_repo)
    await service.initialize_setup_token()
    
    await service.lock_setup()
    
    record = await empty_repo.get_setup_record()
    assert record is not None
    assert record.is_setup_completed is True
    assert record.setup_token is None


@pytest.mark.asyncio
async def test_lock_setup_fails_if_uninitialized(empty_repo: FakeSetupRepository) -> None:
    """Cannot lock if setup was never initialized."""
    service = SetupService(setup_repository=empty_repo)
    with pytest.raises(ValueError, match="Cannot lock an uninitialized setup"):
        await service.lock_setup()

