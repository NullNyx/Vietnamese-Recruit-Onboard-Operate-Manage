"""Unit tests for JobOpeningService — lifecycle transitions and validation.

Tests the Job Opening lifecycle state machine (draft → open → closed/cancelled),
validation of required fields, and audit logging.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.recruitment.application.job_opening_service import (
    JobOpeningService,
    _JOB_OPENING_TRANSITIONS,
)
from src.modules.recruitment.domain.entities import JobOpening
from src.modules.recruitment.domain.enums import JobOpeningStatus
from src.modules.recruitment.domain.exceptions import (
    JobOpeningInvalidStatusTransitionError,
    JobOpeningNotFoundError,
)
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
    # Default to returning a position for create tests
    mock_position = SimpleNamespace(id=uuid4(), name="Senior Developer")
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(first=MagicMock(return_value=mock_position))))
    return session


@pytest.fixture
def user_id():
    """Create a sample user ID."""
    return uuid4()


# ─── Tests ────────────────────────────────────────────────────────────


class TestJobOpeningTransitions:
    """Tests for Job Opening status transitions."""

    def test_draft_can_transition_to_open_and_cancelled(self):
        """Draft should allow transitions to open and cancelled."""
        assert JobOpeningStatus.OPEN in _JOB_OPENING_TRANSITIONS[JobOpeningStatus.DRAFT]
        assert JobOpeningStatus.CANCELLED in _JOB_OPENING_TRANSITIONS[JobOpeningStatus.DRAFT]

    def test_open_can_transition_to_closed_and_cancelled(self):
        """Open should allow transitions to closed and cancelled."""
        assert JobOpeningStatus.CLOSED in _JOB_OPENING_TRANSITIONS[JobOpeningStatus.OPEN]
        assert JobOpeningStatus.CANCELLED in _JOB_OPENING_TRANSITIONS[JobOpeningStatus.OPEN]

    def test_closed_can_reopen(self):
        """Closed should allow transition back to open."""
        assert JobOpeningStatus.OPEN in _JOB_OPENING_TRANSITIONS[JobOpeningStatus.CLOSED]

    def test_cancelled_is_terminal(self):
        """Cancelled should have no valid transitions."""
        assert _JOB_OPENING_TRANSITIONS[JobOpeningStatus.CANCELLED] == []


class TestCreateJobOpening:
    """Tests for creating Job Openings."""

    async def test_create_sets_default_status_to_draft(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Create should default status to draft when not specified."""
        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.create_job_opening(
            title="Senior Developer",
            position_id=uuid4(),
            target_headcount=2,
        )

        assert result.status == JobOpeningStatus.DRAFT

    async def test_create_with_open_status_sets_opened_at(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Create with status=open should set opened_at timestamp."""
        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.create_job_opening(
            title="Senior Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.OPEN,
        )

        assert result.status == JobOpeningStatus.OPEN
        assert result.opened_at is not None


class TestUpdateJobOpening:
    """Tests for updating Job Openings."""

    async def test_update_title(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Update should change the title."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Old Title",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.DRAFT,
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.update_job_opening(
            job_opening_id=job_opening.id,
            title="New Title",
        )

        assert result.title == "New Title"

    async def test_update_nonexistent_raises_error(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Update should raise error for nonexistent Job Opening."""
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=None)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        with pytest.raises(JobOpeningNotFoundError):
            await service.update_job_opening(
                job_opening_id=uuid4(),
                title="New Title",
            )


class TestOpenJobOpening:
    """Tests for opening Job Openings."""

    async def test_open_from_draft(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Opening from draft should succeed."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.DRAFT,
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.open_job_opening(job_opening.id)

        assert result.status == JobOpeningStatus.OPEN
        assert result.opened_at is not None

    async def test_open_from_closed_reopens(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Opening from closed should succeed (reopen)."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.CLOSED,
            closed_at=datetime.now(UTC),
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.open_job_opening(job_opening.id)

        assert result.status == JobOpeningStatus.OPEN

    async def test_open_from_cancelled_fails(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Opening from cancelled should fail."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.CANCELLED,
            cancelled_at=datetime.now(UTC),
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        with pytest.raises(JobOpeningInvalidStatusTransitionError):
            await service.open_job_opening(job_opening.id)


class TestCloseJobOpening:
    """Tests for closing Job Openings."""

    async def test_close_from_open(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Closing from open should succeed."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.OPEN,
            opened_at=datetime.now(UTC),
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.close_job_opening(job_opening.id)

        assert result.status == JobOpeningStatus.CLOSED
        assert result.closed_at is not None

    async def test_close_from_draft_fails(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Closing from draft should fail."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.DRAFT,
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        with pytest.raises(JobOpeningInvalidStatusTransitionError):
            await service.close_job_opening(job_opening.id)


class TestCancelJobOpening:
    """Tests for cancelling Job Openings."""

    async def test_cancel_from_draft(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Cancelling from draft should succeed."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.DRAFT,
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.cancel_job_opening(job_opening.id)

        assert result.status == JobOpeningStatus.CANCELLED
        assert result.cancelled_at is not None

    async def test_cancel_from_open(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Cancelling from open should succeed."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.OPEN,
            opened_at=datetime.now(UTC),
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.cancel_job_opening(job_opening.id)

        assert result.status == JobOpeningStatus.CANCELLED

    async def test_cancel_from_closed_fails(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Cancelling from closed should fail."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.CLOSED,
            closed_at=datetime.now(UTC),
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        with pytest.raises(JobOpeningInvalidStatusTransitionError):
            await service.cancel_job_opening(job_opening.id)

    async def test_cancel_from_cancelled_fails(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Cancelling from cancelled should fail (terminal state)."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.CANCELLED,
            cancelled_at=datetime.now(UTC),
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        with pytest.raises(JobOpeningInvalidStatusTransitionError):
            await service.cancel_job_opening(job_opening.id)


class TestGetJobOpening:
    """Tests for retrieving Job Openings."""

    async def test_get_existing(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Getting existing Job Opening should succeed."""
        job_opening = JobOpening(
            id=uuid4(),
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status=JobOpeningStatus.DRAFT,
        )
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        result = await service.get_job_opening(job_opening.id)

        assert result.id == job_opening.id

    async def test_get_nonexistent_raises_error(
        self, mock_session: AsyncMock, mock_job_opening_repo: AsyncMock, user_id: uuid4
    ):
        """Getting nonexistent Job Opening should raise error."""
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=None)

        service = JobOpeningService(
            session=mock_session,
            job_opening_repo=mock_job_opening_repo,
            user_id=user_id,
        )

        with pytest.raises(JobOpeningNotFoundError):
            await service.get_job_opening(uuid4())
