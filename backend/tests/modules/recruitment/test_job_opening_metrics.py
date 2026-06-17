"""Unit tests for Job Opening summary metrics.

Tests the Job Opening metrics endpoint that returns counts by lifecycle
status (draft, open, closed, cancelled) for HR visibility into recruitment
pipeline health.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.recruitment.application.job_opening_service import JobOpeningService
from src.modules.recruitment.infrastructure.repositories import JobOpeningRepository


# ─── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_job_opening_repo():
    """Create a mock Job Opening repository."""
    repo = AsyncMock(spec=JobOpeningRepository)
    repo.create = AsyncMock(side_effect=lambda j: j)
    repo.update = AsyncMock(side_effect=lambda j: j)
    return repo


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def user_id():
    """Create a sample user ID."""
    return uuid4()


# ─── Tests ────────────────────────────────────────────────────────────

class TestCountJobOpeningsByStatus:
    """Tests for repository count_job_openings_by_status method."""

    async def test_counts_by_status_returns_all_statuses(
        self, mock_session, mock_job_opening_repo
    ):
        """Should return counts for all four statuses."""
        # Mock the execute result to return grouped counts
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("draft", 3),
            ("open", 5),
            ("closed", 2),
            ("cancelled", 1),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_job_openings_by_status()

        assert counts["draft"] == 3
        assert counts["open"] == 5
        assert counts["closed"] == 2
        assert counts["cancelled"] == 1
        assert sum(counts.values()) == 11

    async def test_counts_by_status_handles_empty_table(
        self, mock_session, mock_job_opening_repo
    ):
        """Should return zeros when no Job Openings exist."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_job_openings_by_status()

        assert counts["draft"] == 0
        assert counts["open"] == 0
        assert counts["closed"] == 0
        assert counts["cancelled"] == 0
        assert sum(counts.values()) == 0

    async def test_counts_by_status_handles_partial_statuses(
        self, mock_session, mock_job_opening_repo
    ):
        """Should handle when only some statuses have Job Openings."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("open", 10),
            ("closed", 4),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_job_openings_by_status()

        assert counts["draft"] == 0
        assert counts["open"] == 10
        assert counts["closed"] == 4
        assert counts["cancelled"] == 0


class TestGetSummaryMetrics:
    """Tests for service get_summary_metrics method."""

    async def test_get_summary_metrics_aggregates_correctly(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """Should compute total and per-status counts."""
        mock_job_opening_repo.count_job_openings_by_status = AsyncMock(
            return_value={
                "draft": 3,
                "open": 5,
                "closed": 2,
                "cancelled": 1,
            }
        )

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_summary_metrics()

        assert result["total_job_openings"] == 11
        assert result["draft_count"] == 3
        assert result["open_count"] == 5
        assert result["closed_count"] == 2
        assert result["cancelled_count"] == 1

    async def test_get_summary_metrics_with_zero_totals(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """Should handle zero Job Openings."""
        mock_job_opening_repo.count_job_openings_by_status = AsyncMock(
            return_value={
                "draft": 0,
                "open": 0,
                "closed": 0,
                "cancelled": 0,
            }
        )

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_summary_metrics()

        assert result["total_job_openings"] == 0
        assert result["draft_count"] == 0
        assert result["open_count"] == 0
        assert result["closed_count"] == 0
        assert result["cancelled_count"] == 0


class TestCandidateCountIntegration:
    """Integration tests for candidate counts per Job Opening."""

    async def test_count_candidates_by_status_returns_correct_counts(
        self, mock_session, mock_job_opening_repo
    ):
        """Should return candidate counts grouped by status for each Job Opening."""
        jo_id = uuid4()
        
        # Mock the query result
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (jo_id, "new", 3),
            (jo_id, "reviewing", 2),
            (jo_id, "accepted", 1),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_candidates_by_status([jo_id])

        assert counts[jo_id]["new"] == 3
        assert counts[jo_id]["reviewing"] == 2
        assert counts[jo_id]["accepted"] == 1

    async def test_count_candidates_by_status_empty_list(
        self, mock_session, mock_job_opening_repo
    ):
        """Should return empty dict when given empty list."""
        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_candidates_by_status([])

        assert counts == {}

    async def test_count_candidates_by_status_handles_missing_job_openings(
        self, mock_session, mock_job_opening_repo
    ):
        """Should include Job Opening IDs with no candidates."""
        jo_ids = [uuid4(), uuid4()]
        
        # Mock the query result (empty - no candidates)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_candidates_by_status(jo_ids)

        # Each JO should have an empty dict
        assert counts[jo_ids[0]] == {}
        assert counts[jo_ids[1]] == {}


class TestHeadcountSyncSignals:
    """Tests for filled/overfilled signals in Job Opening responses."""

    async def test_filled_signal_when_accepted_equals_target(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """filled should be True when accepted equals target."""
        jo = SimpleNamespace(
            id=uuid4(),
            title="Test JO",
            position_id=uuid4(),
            target_headcount=2,
            status="open",
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)
        mock_job_opening_repo.count_accepted_by_job_opening = AsyncMock(return_value=2)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_headcount_status(jo.id)

        assert result["filled"] is True
        assert result["overfilled"] is False
        assert result["remaining"] == 0

    async def test_overfilled_signal_when_accepted_exceeds_target(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """overfilled should be True when accepted exceeds target."""
        jo = SimpleNamespace(
            id=uuid4(),
            title="Test JO",
            position_id=uuid4(),
            target_headcount=2,
            status="open",
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)
        mock_job_opening_repo.count_accepted_by_job_opening = AsyncMock(return_value=5)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_headcount_status(jo.id)

        assert result["filled"] is True
        assert result["overfilled"] is True
        assert result["remaining"] == -3

    async def test_remaining_headcount_can_be_negative(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """remaining should be negative when overfilled."""
        jo = SimpleNamespace(
            id=uuid4(),
            title="Test JO",
            position_id=uuid4(),
            target_headcount=1,
            status="open",
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)
        mock_job_opening_repo.count_accepted_by_job_opening = AsyncMock(return_value=3)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_headcount_status(jo.id)

        assert result["remaining"] == -2
