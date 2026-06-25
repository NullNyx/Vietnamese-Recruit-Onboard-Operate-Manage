"""Unit tests for setup gating dependency.

Tests that the `require_setup_completed` dependency properly blocks requests
when the system is not yet initialized.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.modules.identity.container import require_setup_completed


class MockSetupService:
    def __init__(self, is_completed: bool) -> None:
        self._is_completed = is_completed

    async def is_setup_completed(self) -> bool:
        return self._is_completed


@pytest.mark.asyncio
async def test_require_setup_completed_raises_403_when_not_completed() -> None:
    """When setup is not completed, an HTTPException is raised."""
    service = MockSetupService(is_completed=False)
    with pytest.raises(HTTPException) as exc_info:
        await require_setup_completed(setup_service=service)  # type: ignore

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "SETUP_REQUIRED"


@pytest.mark.asyncio
async def test_require_setup_completed_passes_when_completed() -> None:
    """When setup is completed, no exception is raised."""
    service = MockSetupService(is_completed=True)
    # Should not raise any exception
    await require_setup_completed(setup_service=service)  # type: ignore
