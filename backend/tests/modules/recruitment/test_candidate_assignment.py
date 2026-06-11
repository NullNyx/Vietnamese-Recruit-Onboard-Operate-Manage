"""Unit tests for Candidate-to-Job Opening assignment.

Tests the assign, reassign, and unassign flows including validation
rules for Job Opening status, Candidate terminal status, and audit
logging coverage.

Requirements: ADR-0014, Candidate assignment rules per the Backbone Flow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.recruitment.application.candidate_service import CandidateService
from src.modules.recruitment.domain.entities import Candidate, JobOpening
from src.modules.recruitment.domain.enums import CandidateStatus, JobOpeningStatus
from src.modules.recruitment.domain.exceptions import (
    CandidateNotAssignedError,
    CandidateTerminalStatusError,
    JobOpeningNotFoundError,
    JobOpeningNotOpenError,
)
from src.modules.recruitment.infrastructure.repositories import JobOpeningRepository

# ─── Shared fixtures ──────────────────────────────────────────────────

@pytest.fixture
def mock_candidate_repo():
    """Create a mock candidate repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock(side_effect=lambda c: c)
    return repo

@pytest.fixture
def mock_cv_document_repo():
    """Create a mock CV document repository."""
    return AsyncMock()

@pytest.fixture
def mock_minio_client():
    """Create a mock MinIO client."""
    return AsyncMock()

@pytest.fixture
def mock_job_opening_repo():
    """Create a mock Job Opening repository."""
    repo = AsyncMock(spec=JobOpeningRepository)
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    return session

@pytest.fixture
def user_id():
    """Create a test user ID."""
    return uuid4()

@pytest.fixture
def service(
    mock_candidate_repo,
    mock_cv_document_repo,
    mock_minio_client,
    mock_job_opening_repo,
    mock_session,
    user_id,
):
    """Create a CandidateService with mocked dependencies."""
    return CandidateService(
        candidate_repo=mock_candidate_repo,
        cv_document_repo=mock_cv_document_repo,
        minio_client=mock_minio_client,
        session=mock_session,
        user_id=user_id,
        job_opening_repo=mock_job_opening_repo,
    )


# ─── Helpers ───────────────────────────────────────────────────────────

def make_candidate(
    *,
    status: str = CandidateStatus.NEW,
    job_opening_id=None,
) -> Candidate:
    """Create a Candidate with default-override fields."""
    return Candidate(
        id=uuid4(),
        name="Nguyen Van A",
        email="nguyenvana@example.com",
        phone="0123456789",
        status=status,
        job_opening_id=job_opening_id,
    )

def make_job_opening(
    *,
    status: str = JobOpeningStatus.OPEN,
) -> JobOpening:
    """Create a Job Opening with default-override fields."""
    return JobOpening(
        id=uuid4(),
        title="Senior Developer",
        position_id=uuid4(),
        target_headcount=2,
        status=status,
    )


# ─── Assign Tests ──────────────────────────────────────────────────────

class TestAssignToJobOpening:
    """Tests for candidate assignment to a Job Opening."""

    async def test_assign_unassigned_candidate(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning an unassigned Candidate to an open Job Opening succeeds."""
        candidate = make_candidate()
        job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening

        result = await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=job_opening.id,
        )

        assert result.job_opening_id == job_opening.id
        mock_candidate_repo.update.assert_called_once()

    async def test_assign_to_open_job_opening(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assignment is allowed only to Job Openings with status open."""
        candidate = make_candidate()
        job_opening = make_job_opening(status=JobOpeningStatus.OPEN)

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening

        result = await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=job_opening.id,
        )

        assert result.job_opening_id == job_opening.id

    async def test_assign_to_draft_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning to a draft Job Opening is rejected."""
        candidate = make_candidate()
        job_opening = make_job_opening(status=JobOpeningStatus.DRAFT)

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )

    async def test_assign_to_closed_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning to a closed Job Opening is rejected."""
        candidate = make_candidate()
        job_opening = make_job_opening(status=JobOpeningStatus.CLOSED)

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )

    async def test_assign_to_cancelled_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning to a cancelled Job Opening is rejected."""
        candidate = make_candidate()
        job_opening = make_job_opening(status=JobOpeningStatus.CANCELLED)

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )

    async def test_assign_nonexistent_job_opening_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning to a nonexistent Job Opening raises JobOpeningNotFoundError."""
        candidate = make_candidate()

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = None

        with pytest.raises(JobOpeningNotFoundError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=uuid4(),
            )

    async def test_assign_accepted_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning an accepted Candidate is blocked."""
        candidate = make_candidate(status=CandidateStatus.ACCEPTED)
        job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )

    async def test_assign_rejected_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning a rejected Candidate is blocked."""
        candidate = make_candidate(status=CandidateStatus.REJECTED)
        job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )

    async def test_assign_archived_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Assigning an archived Candidate is blocked."""
        candidate = make_candidate(status=CandidateStatus.ARCHIVED)
        job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )

    async def test_assign_exactly_one_at_a_time(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """A Candidate can be assigned to at most one Job Opening at a time."""
        # Assign to first Job Opening
        candidate = make_candidate()
        job_opening_1 = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening_1

        result = await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=job_opening_1.id,
        )
        assert result.job_opening_id == job_opening_1.id

        # Reassign to second Job Opening should update the reference
        job_opening_2 = make_job_opening()
        mock_job_opening_repo.get_by_id.return_value = job_opening_2

        result = await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=job_opening_2.id,
        )
        assert result.job_opening_id == job_opening_2.id
        # The previous assignment is replaced (not dual-assigned)
        assert result.job_opening_id != job_opening_1.id


# ─── Reassign Tests ────────────────────────────────────────────────────

class TestReassignJobOpening:
    """Tests for reassigning a Candidate to a different Job Opening."""

    async def test_reassign_to_different_job_opening(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Reassigning an already-assigned Candidate updates their job_opening_id."""
        candidate = make_candidate(job_opening_id=uuid4())
        new_job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = new_job_opening

        result = await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=new_job_opening.id,
        )

        assert result.job_opening_id == new_job_opening.id

    async def test_reassign_to_same_job_opening(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Reassigning a Candidate to their current Job Opening still succeeds."""
        job_opening = make_job_opening()
        candidate = make_candidate(job_opening_id=job_opening.id)

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening

        result = await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=job_opening.id,
        )

        assert result.job_opening_id == job_opening.id

    async def test_reassign_accepted_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Reassigning an accepted Candidate is blocked."""
        candidate = make_candidate(
            status=CandidateStatus.ACCEPTED,
            job_opening_id=uuid4(),
        )
        job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )


# ─── Unassign Tests ────────────────────────────────────────────────────

class TestUnassignJobOpening:
    """Tests for removing a Candidate's Job Opening assignment."""

    async def test_unassign_assigned_candidate(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Unassigning an assigned Candidate clears job_opening_id."""
        candidate = make_candidate(job_opening_id=uuid4())

        mock_candidate_repo.get_by_id.return_value = candidate

        result = await service.unassign_job_opening(candidate_id=candidate.id)

        assert result.job_opening_id is None

    async def test_unassign_unassigned_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Unassigning an unassigned Candidate raises CandidateNotAssignedError."""
        candidate = make_candidate()

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateNotAssignedError):
            await service.unassign_job_opening(candidate_id=candidate.id)

    async def test_unassign_accepted_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Unassigning an accepted Candidate is blocked."""
        candidate = make_candidate(
            status=CandidateStatus.ACCEPTED,
            job_opening_id=uuid4(),
        )

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.unassign_job_opening(candidate_id=candidate.id)

    async def test_unassign_rejected_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Unassigning a rejected Candidate is blocked."""
        candidate = make_candidate(
            status=CandidateStatus.REJECTED,
            job_opening_id=uuid4(),
        )

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.unassign_job_opening(candidate_id=candidate.id)

    async def test_unassign_archived_candidate_fails(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ):
        """Unassigning an archived Candidate is blocked."""
        candidate = make_candidate(
            status=CandidateStatus.ARCHIVED,
            job_opening_id=uuid4(),
        )

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.unassign_job_opening(candidate_id=candidate.id)


# ─── Terminal Status Guard Tests ───────────────────────────────────────

class TestTerminalStatusGuards:
    """Tests that all terminal statuses block assign/reassign/unassign."""

    @pytest.mark.parametrize(
        "terminal_status",
        [
            CandidateStatus.ACCEPTED,
            CandidateStatus.REJECTED,
            CandidateStatus.ARCHIVED,
        ],
    )
    async def test_all_terminal_statuses_block_assign(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
        terminal_status: str,
    ):
        """All terminal statuses block assignment."""
        candidate = make_candidate(status=terminal_status)
        job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.assign_to_job_opening(
                candidate_id=candidate.id,
                job_opening_id=job_opening.id,
            )

    @pytest.mark.parametrize(
        "terminal_status",
        [
            CandidateStatus.ACCEPTED,
            CandidateStatus.REJECTED,
            CandidateStatus.ARCHIVED,
        ],
    )
    async def test_all_terminal_statuses_block_unassign(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        terminal_status: str,
    ):
        """All terminal statuses block unassignment."""
        candidate = make_candidate(status=terminal_status, job_opening_id=uuid4())

        mock_candidate_repo.get_by_id.return_value = candidate

        with pytest.raises(CandidateTerminalStatusError):
            await service.unassign_job_opening(candidate_id=candidate.id)


# ─── Audit Log Tests ──────────────────────────────────────────────────

class TestAuditLogging:
    """Tests that assignment actions produce audit logs."""

    async def test_assign_creates_audit_log(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
        mock_session: AsyncMock,
    ):
        """Assignment emits a candidate_assigned audit log entry."""
        candidate = make_candidate()
        job_opening = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = job_opening

        await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=job_opening.id,
        )

        # Verify audit log was created (check session.add for audit entries)
        audit_calls = [
            c for c in mock_session.add.call_args_list
            if c[0] and hasattr(c[0][0], 'operation_type')
        ]
        assert len(audit_calls) >= 1
        assert audit_calls[0][0][0].operation_type == "candidate_assigned"

    async def test_reassign_creates_audit_log(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
        mock_session: AsyncMock,
    ):
        """Reassignment emits a candidate_reassigned audit log entry."""
        candidate = make_candidate(job_opening_id=uuid4())
        new_job = make_job_opening()

        mock_candidate_repo.get_by_id.return_value = candidate
        mock_job_opening_repo.get_by_id.return_value = new_job

        await service.assign_to_job_opening(
            candidate_id=candidate.id,
            job_opening_id=new_job.id,
        )

        audit_calls = [
            c for c in mock_session.add.call_args_list
            if c[0] and hasattr(c[0][0], 'operation_type')
        ]
        assert len(audit_calls) >= 1
        assert audit_calls[0][0][0].operation_type == "candidate_reassigned"

    async def test_unassign_creates_audit_log(
        self,
        service: CandidateService,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
        mock_session: AsyncMock,
    ):
        """Unassignment emits a candidate_unassigned audit log entry."""
        candidate = make_candidate(job_opening_id=uuid4())

        mock_candidate_repo.get_by_id.return_value = candidate

        await service.unassign_job_opening(candidate_id=candidate.id)

        audit_calls = [
            c for c in mock_session.add.call_args_list
            if c[0] and hasattr(c[0][0], 'operation_type')
        ]
        assert len(audit_calls) >= 1
        assert audit_calls[0][0][0].operation_type == "candidate_unassigned"
