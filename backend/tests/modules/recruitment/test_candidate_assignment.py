"""Unit tests for Candidate-to-Job Opening assignment flow.

Tests the assign, reassign, and unassign operations on CandidateService,
validating rules: open-only assignment, terminal-status guards, audit logging.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.modules.recruitment.application.candidate_lifecycle_service import (
    CandidateLifecycleService as CandidateService,
)
from src.modules.recruitment.domain.entities import Candidate, JobOpening
from src.modules.recruitment.domain.enums import CandidateStatus, JobOpeningStatus
from src.modules.recruitment.domain.exceptions import (
    CandidateAssignmentBlockedError,
    CandidateNotFoundError,
    InvalidStatusTransitionError,
    JobOpeningNotFoundError,
    JobOpeningNotOpenError,
)
from src.modules.recruitment.infrastructure.repositories import (
    CandidateRepository,
    CVDocumentRepository,
    JobOpeningRepository,
)

# ─── Factories ──────────────────────────────────────────────────────────


def _make_candidate(
    *,
    status: str = CandidateStatus.NEW,
    job_opening_id: UUID | None = None,
    candidate_id: UUID | None = None,
) -> Candidate:
    return Candidate(
        id=uuid4() if candidate_id is None else candidate_id,
        name="Test Candidate",
        email="test@example.com",
        status=status,
        job_opening_id=job_opening_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_job_opening(
    *,
    status: str = JobOpeningStatus.OPEN,
    title: str = "Software Engineer",
    jo_id: UUID | None = None,
) -> JobOpening:
    return JobOpening(
        id=uuid4() if jo_id is None else jo_id,
        title=title,
        position_id=uuid4(),
        target_headcount=2,
        status=status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ─── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def mock_candidate_repo() -> AsyncMock:
    repo = AsyncMock(spec=CandidateRepository)
    repo.update = AsyncMock(side_effect=lambda c: c)
    return repo


@pytest.fixture
def mock_cv_doc_repo() -> AsyncMock:
    return AsyncMock(spec=CVDocumentRepository)


@pytest.fixture
def mock_minio_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_job_opening_repo() -> AsyncMock:
    repo = AsyncMock(spec=JobOpeningRepository)
    return repo


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def service(
    mock_session,
    mock_candidate_repo,
    mock_cv_doc_repo,
    mock_minio_client,
    mock_job_opening_repo,
    user_id,
) -> CandidateService:
    return CandidateService(
        candidate_repo=mock_candidate_repo,
        cv_document_repo=mock_cv_doc_repo,
        minio_client=mock_minio_client,
        session=mock_session,
        user_id=user_id,
        job_opening_repo=mock_job_opening_repo,
    )


# ─── Assign ────────────────────────────────────────────────────────────


class TestAssignCandidate:
    async def test_assign_unassigned_to_open_succeeds(
        self, service, mock_candidate_repo, mock_job_opening_repo, mock_session
    ):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        result = await service.assign_candidate(candidate.id, jo.id)

        assert result.job_opening_id == jo.id
        assert mock_candidate_repo.update.called
        # Audit log written
        assert mock_session.add.called

    async def test_assign_to_non_open_fails(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.CLOSED)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_candidate(candidate.id, jo.id)

    async def test_assign_to_draft_fails(self, service, mock_candidate_repo, mock_job_opening_repo):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.DRAFT)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_candidate(candidate.id, jo.id)

    async def test_assign_to_cancelled_fails(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.CANCELLED)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_candidate(candidate.id, jo.id)

    async def test_assign_nonexistent_job_opening_fails(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(JobOpeningNotFoundError):
            await service.assign_candidate(candidate.id, uuid4())

    async def test_assign_already_assigned_fails(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        existing_jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=existing_jo_id)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(InvalidStatusTransitionError):
            await service.assign_candidate(candidate.id, jo.id)

    async def test_assign_accepted_candidate_blocked(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        candidate = _make_candidate(status=CandidateStatus.ACCEPTED, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(CandidateAssignmentBlockedError):
            await service.assign_candidate(candidate.id, jo.id)

    async def test_assign_rejected_candidate_blocked(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        candidate = _make_candidate(status=CandidateStatus.REJECTED, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(CandidateAssignmentBlockedError):
            await service.assign_candidate(candidate.id, jo.id)

    async def test_assign_archived_candidate_blocked(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        candidate = _make_candidate(status=CandidateStatus.ARCHIVED, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(CandidateAssignmentBlockedError):
            await service.assign_candidate(candidate.id, jo.id)

    @pytest.mark.parametrize(
        "status",
        [
            CandidateStatus.NEW,
            CandidateStatus.REVIEWING,
            CandidateStatus.INTERVIEW_SCHEDULED,
        ],
    )
    async def test_assign_allowed_from_status(
        self, service, mock_candidate_repo, mock_job_opening_repo, mock_session, status
    ):
        candidate = _make_candidate(status=status, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        result = await service.assign_candidate(candidate.id, jo.id)

        assert result.job_opening_id == jo.id

    async def test_assign_nonexistent_candidate_fails(self, service, mock_candidate_repo):
        mock_candidate_repo.get_by_id = AsyncMock(return_value=None)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=None)

        with pytest.raises(CandidateNotFoundError):
            await service.assign_candidate(uuid4(), uuid4())


# ─── Reassign ──────────────────────────────────────────────────────────


class TestReassignCandidate:
    async def test_reassign_to_different_open_jo_succeeds(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        old_jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.REVIEWING, job_opening_id=old_jo_id)
        new_jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=new_jo)

        result = await service.reassign_candidate(candidate.id, new_jo.id)

        assert result.job_opening_id == new_jo.id

    async def test_reassign_to_same_jo_is_noop(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=jo.id)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        result = await service.reassign_candidate(candidate.id, jo.id)

        assert result.job_opening_id == jo.id
        mock_candidate_repo.update.assert_not_called()

    async def test_reassign_when_not_assigned_fails(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(InvalidStatusTransitionError):
            await service.reassign_candidate(candidate.id, jo.id)

    async def test_reassign_to_non_open_jo_fails(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        old_jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=old_jo_id)
        jo = _make_job_opening(status=JobOpeningStatus.CLOSED)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(JobOpeningNotOpenError):
            await service.reassign_candidate(candidate.id, jo.id)

    async def test_reassign_terminal_status_blocked(
        self, service, mock_candidate_repo, mock_job_opening_repo
    ):
        jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.ACCEPTED, job_opening_id=jo_id)
        new_jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=new_jo)

        with pytest.raises(CandidateAssignmentBlockedError):
            await service.reassign_candidate(candidate.id, new_jo.id)

    @pytest.mark.parametrize(
        "status",
        [
            CandidateStatus.NEW,
            CandidateStatus.REVIEWING,
            CandidateStatus.INTERVIEW_SCHEDULED,
        ],
    )
    async def test_reassign_allowed_from_status(
        self, service, mock_candidate_repo, mock_job_opening_repo, status
    ):
        old_jo_id = uuid4()
        candidate = _make_candidate(status=status, job_opening_id=old_jo_id)
        new_jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=new_jo)

        result = await service.reassign_candidate(candidate.id, new_jo.id)

        assert result.job_opening_id == new_jo.id


# ─── Unassign ──────────────────────────────────────────────────────────


class TestUnassignCandidate:
    async def test_unassign_succeeds(self, service, mock_candidate_repo):
        jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=jo_id)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)

        result = await service.unassign_candidate(candidate.id)

        assert result.job_opening_id is None

    async def test_unassign_when_not_assigned_fails(self, service, mock_candidate_repo):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)

        with pytest.raises(InvalidStatusTransitionError):
            await service.unassign_candidate(candidate.id)

    async def test_unassign_terminal_status_blocked(self, service, mock_candidate_repo):
        jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.ACCEPTED, job_opening_id=jo_id)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)

        with pytest.raises(CandidateAssignmentBlockedError):
            await service.unassign_candidate(candidate.id)

    async def test_unassign_rejected_blocked(self, service, mock_candidate_repo):
        jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.REJECTED, job_opening_id=jo_id)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)

        with pytest.raises(CandidateAssignmentBlockedError):
            await service.unassign_candidate(candidate.id)

    async def test_unassign_archived_blocked(self, service, mock_candidate_repo):
        jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.ARCHIVED, job_opening_id=jo_id)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)

        with pytest.raises(CandidateAssignmentBlockedError):
            await service.unassign_candidate(candidate.id)

    @pytest.mark.parametrize(
        "status",
        [
            CandidateStatus.NEW,
            CandidateStatus.REVIEWING,
            CandidateStatus.INTERVIEW_SCHEDULED,
        ],
    )
    async def test_unassign_allowed_from_status(self, service, mock_candidate_repo, status):
        jo_id = uuid4()
        candidate = _make_candidate(status=status, job_opening_id=jo_id)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)

        result = await service.unassign_candidate(candidate.id)

        assert result.job_opening_id is None


# ─── Audit Logging ─────────────────────────────────────────────────────


class TestAssignmentAuditLogging:
    async def test_assign_emits_audit_log(
        self, service, mock_candidate_repo, mock_job_opening_repo, mock_session
    ):
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        await service.assign_candidate(candidate.id, jo.id)

        audit_calls = [
            c
            for c in mock_session.add.call_args_list
            if c[0] and hasattr(c[0][0], "operation_type")
        ]
        assert len(audit_calls) >= 1
        assert audit_calls[0][0][0].operation_type == "candidate_assigned"
        assert audit_calls[0][0][0].new_value == {"job_opening_id": str(jo.id)}

    async def test_reassign_emits_audit_log(
        self, service, mock_candidate_repo, mock_job_opening_repo, mock_session
    ):
        old_jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=old_jo_id)
        new_jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=new_jo)

        await service.reassign_candidate(candidate.id, new_jo.id)

        audit_calls = [
            c
            for c in mock_session.add.call_args_list
            if c[0] and hasattr(c[0][0], "operation_type")
        ]
        assert len(audit_calls) >= 1
        assert audit_calls[0][0][0].operation_type == "candidate_reassigned"
        assert audit_calls[0][0][0].previous_value == {"job_opening_id": str(old_jo_id)}
        assert audit_calls[0][0][0].new_value == {"job_opening_id": str(new_jo.id)}

    async def test_unassign_emits_audit_log(self, service, mock_candidate_repo, mock_session):
        jo_id = uuid4()
        candidate = _make_candidate(status=CandidateStatus.NEW, job_opening_id=jo_id)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)
        mock_candidate_repo.get_by_id_for_update = AsyncMock(return_value=candidate)

        await service.unassign_candidate(candidate.id)

        audit_calls = [
            c
            for c in mock_session.add.call_args_list
            if c[0] and hasattr(c[0][0], "operation_type")
        ]
        assert len(audit_calls) >= 1
        assert audit_calls[0][0][0].operation_type == "candidate_unassigned"
        assert audit_calls[0][0][0].previous_value == {"job_opening_id": str(jo_id)}
        assert audit_calls[0][0][0].new_value == {"job_opening_id": None}


# ─── Headcount Sync Tests ──────────────────────────────────────────────


class TestCandidateAcceptanceHeadcountSync:
    """Tests for Job Opening headcount sync when candidate is accepted."""

    async def test_accept_candidate_with_job_opening_updates_timestamp(
        self,
        mock_session: AsyncMock,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
        mock_cv_doc_repo,
        mock_minio_client,
        user_id: uuid4,
    ):
        """Accepting a candidate assigned to Job Opening should update Job Opening timestamp."""
        from datetime import UTC, datetime

        job_opening_id = uuid4()
        candidate = _make_candidate(
            status=CandidateStatus.INTERVIEW_SCHEDULED,
            job_opening_id=job_opening_id,
        )
        job_opening = SimpleNamespace(
            id=job_opening_id,
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status="open",
            updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        )

        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.update = AsyncMock(side_effect=lambda c: c)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)
        mock_job_opening_repo.update = AsyncMock(side_effect=lambda j: j)
        mock_session.commit = AsyncMock()

        from src.modules.recruitment.application.candidate_lifecycle_service import (
            CandidateLifecycleService as CandidateService,
        )

        candidate_service = CandidateService(
            candidate_repo=mock_candidate_repo,
            cv_document_repo=mock_cv_doc_repo,
            minio_client=mock_minio_client,
            session=mock_session,
            user_id=user_id,
            job_opening_repo=mock_job_opening_repo,
        )

        result = await candidate_service.accept_candidate(candidate.id)

        assert result.status == CandidateStatus.ACCEPTED
        assert result.job_opening_id == job_opening_id
        # Job Opening should be touched when candidate has job_opening_id
        mock_job_opening_repo.get_by_id.assert_called_once()
        mock_job_opening_repo.update.assert_called_once()

    async def test_accept_candidate_without_job_opening_skips_update(
        self,
        mock_session: AsyncMock,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
        mock_cv_doc_repo,
        mock_minio_client,
        user_id: uuid4,
    ):
        """Accepting a candidate without Job Opening should not call Job Opening repo."""
        candidate = _make_candidate(
            status=CandidateStatus.INTERVIEW_SCHEDULED,
            job_opening_id=None,
        )

        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.update = AsyncMock(side_effect=lambda c: c)
        mock_session.commit = AsyncMock()

        from src.modules.recruitment.application.candidate_lifecycle_service import (
            CandidateLifecycleService as CandidateService,
        )

        candidate_service = CandidateService(
            candidate_repo=mock_candidate_repo,
            cv_document_repo=mock_cv_doc_repo,
            minio_client=mock_minio_client,
            session=mock_session,
            user_id=user_id,
            job_opening_repo=mock_job_opening_repo,
        )

        result = await candidate_service.accept_candidate(candidate.id)

        assert result.status == CandidateStatus.ACCEPTED
        mock_job_opening_repo.get_by_id.assert_not_called()
        mock_job_opening_repo.update.assert_not_called()

    async def test_accept_candidate_not_blocked_when_filled(
        self,
        mock_session: AsyncMock,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
        mock_cv_doc_repo,
        mock_minio_client,
        user_id: uuid4,
    ):
        """Accepting a candidate for a filled Job Opening should NOT be blocked."""
        job_opening_id = uuid4()
        candidate = _make_candidate(
            status=CandidateStatus.INTERVIEW_SCHEDULED,
            job_opening_id=job_opening_id,
        )
        job_opening = SimpleNamespace(
            id=job_opening_id,
            title="Developer",
            position_id=uuid4(),
            target_headcount=2,
            status="open",
            updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        )

        mock_job_opening_repo.get_by_id = AsyncMock(return_value=job_opening)
        mock_job_opening_repo.count_accepted_by_job_opening = AsyncMock(return_value=2)
        mock_job_opening_repo.update = AsyncMock(side_effect=lambda j: j)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=candidate)
        mock_candidate_repo.update = AsyncMock(side_effect=lambda c: c)
        mock_session.commit = AsyncMock()

        from src.modules.recruitment.application.candidate_lifecycle_service import (
            CandidateLifecycleService as CandidateService,
        )

        candidate_service = CandidateService(
            candidate_repo=mock_candidate_repo,
            cv_document_repo=mock_cv_doc_repo,
            minio_client=mock_minio_client,
            session=mock_session,
            user_id=user_id,
            job_opening_repo=mock_job_opening_repo,
        )

        # This should NOT raise - overfill is allowed
        result = await candidate_service.accept_candidate(candidate.id)

        assert result.status == CandidateStatus.ACCEPTED
