"""Unit tests for JobApplication assignment and promotion service layer.

Tests the assign_to_job_opening and promote_to_candidate methods on
JobApplicationService, validating rules: dismissed blocked, open-only
assignment, idempotent promotion, missing-field validation, audit history.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.modules.recruitment.application.job_application_decision_service import (
    JobApplicationDecisionService,
)
from src.modules.recruitment.application.job_application_service import JobApplicationService
from src.modules.recruitment.domain.entities import Candidate, JobApplication, JobOpening
from src.modules.recruitment.domain.enums import (
    ApplicationSource,
    CandidateStatus,
    JobApplicationStatus,
    JobOpeningStatus,
)
from src.modules.recruitment.domain.exceptions import (
    JobApplicationAssignmentBlockedError,
    JobApplicationNotFoundError,
    JobApplicationPromotionBlockedError,
    JobOpeningNotFoundError,
    JobOpeningNotOpenError,
)
from src.modules.recruitment.infrastructure.repositories import (
    CandidateRepository,
    JobApplicationRepository,
    JobOpeningRepository,
)

# ─── Factories ──────────────────────────────────────────────────────────


def _make_job_application(
    *,
    status: str = JobApplicationStatus.NEW,
    job_opening_id: UUID | None = None,
    candidate_id: UUID | None = None,
    applicant_name: str | None = "Test Applicant",
    applicant_email: str | None = "applicant@example.com",
    app_id: UUID | None = None,
) -> JobApplication:
    return JobApplication(
        id=uuid4() if app_id is None else app_id,
        source_email_message_id=uuid4(),
        gmail_message_id="msg_123",
        gmail_thread_id="thread_123",
        source=ApplicationSource.DIRECT,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        sender_name="Sender",
        sender_email="sender@example.com",
        status=status,
        job_opening_id=job_opening_id,
        candidate_id=candidate_id,
        audit_history=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_candidate(
    *,
    candidate_id: UUID | None = None,
    name: str = "Promoted Candidate",
    email: str = "candidate@example.com",
    job_opening_id: UUID | None = None,
) -> Candidate:
    return Candidate(
        id=uuid4() if candidate_id is None else candidate_id,
        name=name,
        email=email,
        job_opening_id=job_opening_id,
        status=CandidateStatus.NEW,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_job_opening(
    *,
    status: str = JobOpeningStatus.OPEN,
    jo_id: UUID | None = None,
) -> JobOpening:
    return JobOpening(
        id=uuid4() if jo_id is None else jo_id,
        title="Software Engineer",
        position_id=uuid4(),
        target_headcount=2,
        status=status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ─── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def mock_ja_repo() -> AsyncMock:
    repo = AsyncMock(spec=JobApplicationRepository)
    repo.update = AsyncMock(side_effect=lambda ja: ja)
    repo.create = AsyncMock(side_effect=lambda ja: ja)
    return repo


@pytest.fixture
def mock_candidate_repo() -> AsyncMock:
    repo = AsyncMock(spec=CandidateRepository)
    repo.create = AsyncMock(side_effect=lambda c: c)
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_job_opening_repo() -> AsyncMock:
    repo = AsyncMock(spec=JobOpeningRepository)
    return repo


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def service(
    mock_ja_repo: AsyncMock,
    mock_candidate_repo: AsyncMock,
    mock_job_opening_repo: AsyncMock,
) -> JobApplicationDecisionService:
    return JobApplicationDecisionService(
        session=AsyncMock(),
        job_application_repo=mock_ja_repo,
        candidate_repo=mock_candidate_repo,
        job_opening_repo=mock_job_opening_repo,
    )


class TestAutomationBoundary:
    def test_ingestion_service_exposes_no_promotion_interface(
        self, mock_ja_repo: AsyncMock
    ) -> None:
        ingestion = JobApplicationService(
            session=AsyncMock(),
            job_application_repo=mock_ja_repo,
        )

        assert not hasattr(ingestion, "promote_to_candidate")
        assert not hasattr(ingestion, "assign_to_job_opening")


# ─── Assign to Job Opening ─────────────────────────────────────────────


class TestAssignToJobOpening:
    async def test_hr_can_correct_application_source_with_audit_trail(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        application = _make_job_application(status=JobApplicationStatus.NEW)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=application)
        hr_user_id = uuid4()

        result = await service.correct_source(
            application.id, ApplicationSource.AGENCY, user_id=hr_user_id
        )

        assert result.source == ApplicationSource.AGENCY
        assert result.audit_history[-1] == {
            "action": "source_corrected",
            "previous_source": ApplicationSource.DIRECT,
            "corrected_source": ApplicationSource.AGENCY,
            "performed_by_user_id": str(hr_user_id),
            "occurred_at": result.audit_history[-1]["occurred_at"],
        }
        mock_ja_repo.update.assert_awaited_once_with(application)

    async def test_assign_unassigned_to_open_succeeds(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        result = await service.assign_to_job_opening(ja.id, jo.id, user_id=uuid4())

        assert result.job_opening_id == jo.id
        assert mock_ja_repo.update.called
        # Verify audit history was appended
        assert len(result.audit_history) == 1
        assert result.audit_history[0]["action"] == "assignment_updated"

    async def test_assign_to_non_open_fails(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.CLOSED)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_to_job_opening(ja.id, jo.id)

    async def test_assign_to_draft_fails(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW, job_opening_id=None)
        jo = _make_job_opening(status=JobOpeningStatus.DRAFT)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(JobOpeningNotOpenError):
            await service.assign_to_job_opening(ja.id, jo.id)

    async def test_assign_dismissed_blocks(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.DISMISSED, job_opening_id=None)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        with pytest.raises(JobApplicationAssignmentBlockedError):
            await service.assign_to_job_opening(ja.id, uuid4())

    async def test_assign_promoted_application_blocks(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        ja = _make_job_application(
            status=JobApplicationStatus.PROMOTED,
            candidate_id=uuid4(),
        )
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        with pytest.raises(JobApplicationAssignmentBlockedError):
            await service.assign_to_job_opening(ja.id, uuid4())

    async def test_unassign_succeeds(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        jo_id = uuid4()
        ja = _make_job_application(status=JobApplicationStatus.NEW, job_opening_id=jo_id)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        result = await service.assign_to_job_opening(ja.id, None, user_id=uuid4())

        assert result.job_opening_id is None
        assert len(result.audit_history) == 1
        assert result.audit_history[0]["action"] == "assignment_updated"

    async def test_assign_nonexistent_ja_fails(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=None)

        with pytest.raises(JobApplicationNotFoundError):
            await service.assign_to_job_opening(uuid4(), uuid4())

    async def test_assign_nonexistent_jo_fails(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW, job_opening_id=None)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(JobOpeningNotFoundError):
            await service.assign_to_job_opening(ja.id, uuid4())


# ─── Promote to Candidate ──────────────────────────────────────────────


class TestPromoteToCandidate:
    async def test_promote_valid_ja_succeeds(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_candidate_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(
            status=JobApplicationStatus.NEW,
            applicant_name="Nguyen Van A",
            applicant_email="a@example.com",
        )
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        app, candidate = await service.promote_to_candidate(
            ja.id,
            applicant_name="Nguyen Van A",
            applicant_email="a@example.com",
            user_id=uuid4(),
        )

        assert candidate.name == "Nguyen Van A"
        assert candidate.email == "a@example.com"
        assert app.candidate_id == candidate.id
        assert app.status == JobApplicationStatus.PROMOTED
        assert mock_candidate_repo.create.called
        assert mock_ja_repo.update.called
        # Audit history appended
        assert len(app.audit_history) == 1
        assert app.audit_history[0]["action"] == "promoted_to_candidate"

    async def test_promote_dismissed_fails(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.DISMISSED)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        with pytest.raises(JobApplicationPromotionBlockedError):
            await service.promote_to_candidate(
                ja.id, applicant_name="Test", applicant_email="test@example.com"
            )

    async def test_promote_missing_name_fails(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW, applicant_name=None)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        with pytest.raises(JobApplicationPromotionBlockedError):
            await service.promote_to_candidate(
                ja.id, applicant_name="", applicant_email="test@example.com"
            )

    async def test_promote_missing_email_fails(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW, applicant_email=None)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        with pytest.raises(JobApplicationPromotionBlockedError):
            await service.promote_to_candidate(ja.id, applicant_name="Test", applicant_email="")

    async def test_promote_with_job_opening(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_candidate_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW)
        jo = _make_job_opening(status=JobOpeningStatus.OPEN)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        app, candidate = await service.promote_to_candidate(
            ja.id,
            applicant_name="Nguyen Van A",
            applicant_email="a@example.com",
            job_opening_id=jo.id,
            user_id=uuid4(),
        )

        assert candidate.job_opening_id == jo.id
        assert app.job_opening_id == jo.id
        assert app.candidate_id == candidate.id

    async def test_promote_preserves_existing_job_opening_assignment(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
    ) -> None:
        job_opening_id = uuid4()
        ja = _make_job_application(
            status=JobApplicationStatus.NEW,
            job_opening_id=job_opening_id,
        )
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        app, candidate = await service.promote_to_candidate(
            ja.id,
            applicant_name="Nguyen Van A",
            applicant_email="a@example.com",
        )

        assert app.job_opening_id == job_opening_id
        assert candidate.job_opening_id == job_opening_id

    async def test_promote_to_nonexistent_jo_fails(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(JobOpeningNotFoundError):
            await service.promote_to_candidate(
                ja.id,
                applicant_name="Test",
                applicant_email="test@example.com",
                job_opening_id=uuid4(),
            )

    async def test_promote_to_non_open_jo_fails(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_job_opening_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW)
        jo = _make_job_opening(status=JobOpeningStatus.CANCELLED)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_job_opening_repo.get_by_id = AsyncMock(return_value=jo)

        with pytest.raises(JobOpeningNotOpenError):
            await service.promote_to_candidate(
                ja.id,
                applicant_name="Test",
                applicant_email="test@example.com",
                job_opening_id=jo.id,
            )

    async def test_promote_nonexistent_ja_fails(
        self, service: JobApplicationDecisionService, mock_ja_repo: AsyncMock
    ) -> None:
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=None)

        with pytest.raises(JobApplicationNotFoundError):
            await service.promote_to_candidate(
                uuid4(), applicant_name="Test", applicant_email="test@example.com"
            )

    async def test_promote_idempotent_returns_same(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_candidate_repo: AsyncMock,
    ) -> None:
        existing_candidate = _make_candidate(name="Nguyen Van A", email="a@example.com")
        ja = _make_job_application(
            status=JobApplicationStatus.PROMOTED,
            candidate_id=existing_candidate.id,
        )
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)
        mock_candidate_repo.get_by_id = AsyncMock(return_value=existing_candidate)

        app, candidate = await service.promote_to_candidate(
            ja.id,
            applicant_name="Nguyen Van A",
            applicant_email="a@example.com",
        )

        assert candidate.id == existing_candidate.id
        assert candidate.name == "Nguyen Van A"
        assert app.candidate_id == existing_candidate.id
        # Should NOT create a new candidate
        mock_candidate_repo.create.assert_not_called()

    async def test_promote_sets_source_email_message_id(
        self,
        service: JobApplicationDecisionService,
        mock_ja_repo: AsyncMock,
        mock_candidate_repo: AsyncMock,
    ) -> None:
        ja = _make_job_application(status=JobApplicationStatus.NEW)
        mock_ja_repo.get_by_id_for_update = AsyncMock(return_value=ja)

        _, candidate = await service.promote_to_candidate(
            ja.id, applicant_name="Test", applicant_email="test@example.com"
        )

        assert candidate.source_email_message_id == ja.source_email_message_id
