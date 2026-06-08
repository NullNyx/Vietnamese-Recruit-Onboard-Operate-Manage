"""Tests for the onboarding event consumer.

Verifies the process_candidate_accepted ARQ task function correctly consumes
candidate_accepted events and creates OnboardingProcess records.

Requirements: runtime backbone wiring
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.onboarding.container import process_candidate_accepted
from src.modules.onboarding.domain.enums import OnboardingStatus


@pytest.fixture
def mock_session_maker():
    """Mock session maker that yields a mock session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()

    session_maker = MagicMock()
    session_maker.return_value.__aenter__ = AsyncMock(return_value=session)
    session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

    return session_maker, session


@pytest.fixture
def mock_onboarding_service():
    """Mock OnboardingService."""
    service = MagicMock()
    service.start_from_event = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_process_candidate_accepted_creates_onboarding(
    mock_session_maker, mock_onboarding_service
):
    """Consumer creates OnboardingProcess when processing valid event."""
    session_maker, session = mock_session_maker

    ctx = {
        "session_maker": session_maker,
        "job_id": "test-job-123",
        "job_try": 1,
    }

    payload = {
        "candidate_id": str(uuid4()),
        "name": "Nguyen Van A",
        "email": "nguyen.van.a@example.com",
    }

    with patch(
        "src.modules.onboarding.container._build_service",
        return_value=mock_onboarding_service
    ):
        await process_candidate_accepted(ctx, payload)

    from uuid import UUID as _UUID
    mock_onboarding_service.start_from_event.assert_awaited_once_with(
        candidate_id=_UUID(payload["candidate_id"]),
        full_name=payload["name"],
        email=payload["email"],
        event_id="test-job-123",
    )


@pytest.mark.asyncio
async def test_process_candidate_accepted_rejects_malformed_event(
    mock_session_maker, mock_onboarding_service
):
    """Consumer rejects malformed events without calling service."""
    session_maker, session = mock_session_maker

    ctx = {
        "session_maker": session_maker,
        "job_id": "test-job-456",
        "job_try": 1,
    }

    # Missing required 'email' field
    payload = {
        "candidate_id": str(uuid4()),
        "name": "Tran Thi B",
    }

    with patch(
        "src.modules.onboarding.container._build_service",
        return_value=mock_onboarding_service
    ):
        result = await process_candidate_accepted(ctx, payload)

    # Service should not be called for malformed events
    mock_onboarding_service.start_from_event.assert_not_called()


@pytest.mark.asyncio
async def test_process_candidate_accepted_retries_on_transient_error(
    mock_session_maker, mock_onboarding_service
):
    """Consumer re-raises transient errors for ARQ retry."""
    session_maker, session = mock_session_maker

    ctx = {
        "session_maker": session_maker,
        "job_id": "test-job-789",
        "job_try": 1,  # Not final attempt
        "max_tries": 3,
    }

    payload = {
        "candidate_id": str(uuid4()),
        "name": "Le Van C",
        "email": "le.van.c@example.com",
    }

    mock_onboarding_service.start_from_event = AsyncMock(
        side_effect=Exception("Database connection lost")
    )

    with patch(
        "src.modules.onboarding.container._build_service",
        return_value=mock_onboarding_service
    ):
        with pytest.raises(Exception, match="Database connection lost"):
            await process_candidate_accepted(ctx, payload)


@pytest.mark.asyncio
async def test_process_candidate_accepted_records_failure_on_final_attempt(
    mock_session_maker, mock_onboarding_service
):
    """Consumer records failure audit on final retry attempt."""
    session_maker, session = mock_session_maker

    ctx = {
        "session_maker": session_maker,
        "job_id": "test-job-final",
        "job_try": 3,  # Final attempt
        "max_tries": 3,
    }

    payload = {
        "candidate_id": str(uuid4()),
        "name": "Pham Van D",
        "email": "pham.van.d@example.com",
    }

    mock_onboarding_service.start_from_event = AsyncMock(
        side_effect=Exception("Permanent failure")
    )

    with patch(
        "src.modules.onboarding.container._build_service",
        return_value=mock_onboarding_service
    ):
        with patch(
            "src.modules.onboarding.container.OnboardingAuditRepository"
        ) as mock_audit_repo:
            mock_audit_instance = MagicMock()
            mock_audit_instance.append = AsyncMock()
            mock_audit_repo.return_value = mock_audit_instance

            with pytest.raises(Exception, match="Permanent failure"):
                await process_candidate_accepted(ctx, payload)

            # Verify failure audit was recorded
            mock_audit_instance.append.assert_awaited_once()
            audit_entry = mock_audit_instance.append.call_args[0][0]
            assert audit_entry.operation_type == "event_failed"
            assert audit_entry.success is False
