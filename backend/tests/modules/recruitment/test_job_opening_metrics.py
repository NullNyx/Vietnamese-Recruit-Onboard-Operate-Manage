"""Unit tests for Job Opening summary metrics.

Tests the Job Opening metrics endpoint that returns counts by lifecycle
status (draft, open, closed, cancelled). Uses JobOpening domain entities
for realistic fixture data and covers all Candidate statuses.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.modules.recruitment.application.job_opening_service import JobOpeningService
from src.modules.recruitment.domain.entities import JobOpening
from src.modules.recruitment.domain.enums import CandidateStatus, JobOpeningStatus
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


# ─── Test: Repository count_job_openings_by_status ────────────────────

class TestCountJobOpeningsByStatus:
    """Tests for repository count_job_openings_by_status method."""

    async def test_counts_by_status_returns_all_statuses(self, mock_session):
        """Should return counts for all four lifecycle statuses."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (JobOpeningStatus.DRAFT, 3),
            (JobOpeningStatus.OPEN, 5),
            (JobOpeningStatus.CLOSED, 2),
            (JobOpeningStatus.CANCELLED, 1),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_job_openings_by_status()

        assert counts[JobOpeningStatus.DRAFT] == 3
        assert counts[JobOpeningStatus.OPEN] == 5
        assert counts[JobOpeningStatus.CLOSED] == 2
        assert counts[JobOpeningStatus.CANCELLED] == 1

    async def test_counts_by_status_handles_empty_table(self, mock_session):
        """Should return zeros when no Job Openings exist."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_job_openings_by_status()

        assert all(v == 0 for v in counts.values())

    async def test_counts_by_status_handles_partial_statuses(self, mock_session):
        """Should handle when only some statuses have Job Openings."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (JobOpeningStatus.OPEN, 10),
            (JobOpeningStatus.CLOSED, 4),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_job_openings_by_status()

        assert counts[JobOpeningStatus.DRAFT] == 0
        assert counts[JobOpeningStatus.OPEN] == 10
        assert counts[JobOpeningStatus.CLOSED] == 4
        assert counts[JobOpeningStatus.CANCELLED] == 0


# ─── Test: Service get_summary_metrics ────────────────────────────────

class TestGetSummaryMetrics:
    """Tests for service get_summary_metrics method."""

    async def test_get_summary_metrics_aggregates_correctly(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """Should compute total and per-status counts."""
        mock_job_opening_repo.count_job_openings_by_status = AsyncMock(
            return_value={
                JobOpeningStatus.DRAFT: 3,
                JobOpeningStatus.OPEN: 5,
                JobOpeningStatus.CLOSED: 2,
                JobOpeningStatus.CANCELLED: 1,
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
                JobOpeningStatus.DRAFT: 0,
                JobOpeningStatus.OPEN: 0,
                JobOpeningStatus.CLOSED: 0,
                JobOpeningStatus.CANCELLED: 0,
            }
        )

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_summary_metrics()

        assert result["total_job_openings"] == 0


# ─── Test: Candidate counts per Job Opening (all 6 statuses) ──────────

class TestCandidateCountPerJobOpening:
    """Tests for candidate counts grouped by status per Job Opening.

    Covers all 6 Candidate lifecycle statuses: new, reviewing,
    interview_scheduled, accepted, rejected, archived.
    """

    async def test_count_candidates_by_status_returns_all_six_statuses(
        self, mock_session,
    ):
        """Should return counts for all 6 candidate statuses."""
        jo_id = uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (jo_id, CandidateStatus.NEW, 5),
            (jo_id, CandidateStatus.REVIEWING, 3),
            (jo_id, CandidateStatus.INTERVIEW_SCHEDULED, 2),
            (jo_id, CandidateStatus.ACCEPTED, 4),
            (jo_id, CandidateStatus.REJECTED, 6),
            (jo_id, CandidateStatus.ARCHIVED, 1),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_candidates_by_status([jo_id])

        assert counts[jo_id][CandidateStatus.NEW] == 5
        assert counts[jo_id][CandidateStatus.REVIEWING] == 3
        assert counts[jo_id][CandidateStatus.INTERVIEW_SCHEDULED] == 2
        assert counts[jo_id][CandidateStatus.ACCEPTED] == 4
        assert counts[jo_id][CandidateStatus.REJECTED] == 6
        assert counts[jo_id][CandidateStatus.ARCHIVED] == 1
        assert sum(counts[jo_id].values()) == 21

    async def test_count_candidates_by_status_empty_list(self, mock_session):
        """Should return empty dict when given empty list."""
        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_candidates_by_status([])
        assert counts == {}

    async def test_count_candidates_by_status_partial_counts(
        self, mock_session,
    ):
        """Should handle Job Openings with only some statuses populated."""
        jo_ids = [uuid4(), uuid4()]

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (jo_ids[0], CandidateStatus.NEW, 2),
            (jo_ids[0], CandidateStatus.ACCEPTED, 1),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_candidates_by_status(jo_ids)

        assert counts[jo_ids[0]][CandidateStatus.NEW] == 2
        assert counts[jo_ids[0]][CandidateStatus.ACCEPTED] == 1
        assert counts[jo_ids[1]] == {}

    async def test_count_candidates_by_status_multiple_job_openings(
        self, mock_session,
    ):
        """Should aggregate across multiple Job Openings."""
        jo_a = uuid4()
        jo_b = uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (jo_a, CandidateStatus.NEW, 3),
            (jo_a, CandidateStatus.REJECTED, 1),
            (jo_b, CandidateStatus.INTERVIEW_SCHEDULED, 1),
            (jo_b, CandidateStatus.ACCEPTED, 2),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = JobOpeningRepository(mock_session)
        counts = await repo.count_candidates_by_status([jo_a, jo_b])

        assert sum(counts[jo_a].values()) == 4
        assert sum(counts[jo_b].values()) == 3


# ─── Test: Headcount sync with real JobOpening entities ──────────────

class TestHeadcountSyncWithRealEntities:
    """Tests for filled/overfilled signals using real JobOpening entities."""

    async def test_filled_when_accepted_equals_target(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """filled should be True when accepted equals target."""
        jo = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.OPEN,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
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

    async def test_overfilled_when_accepted_exceeds_target(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """overfilled should be True when accepted exceeds target."""
        jo = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.OPEN,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
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

    async def test_not_filled_when_accepted_below_target(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """filled should be False when accepted is below target."""
        jo = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=5,
            status=JobOpeningStatus.OPEN,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)
        mock_job_opening_repo.count_accepted_by_job_opening = AsyncMock(return_value=2)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_headcount_status(jo.id)

        assert result["filled"] is False
        assert result["overfilled"] is False
        assert result["remaining"] == 3

    async def test_nonexistent_job_opening_raises_error(
        self, mock_session, mock_job_opening_repo, user_id
    ):
        """get_headcount_status should raise error for nonexistent Job Opening."""
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=None)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        from src.modules.recruitment.domain.exceptions import JobOpeningNotFoundError

        with pytest.raises(JobOpeningNotFoundError):
            await service.get_headcount_status(uuid4())
