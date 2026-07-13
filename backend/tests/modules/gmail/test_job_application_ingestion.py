"""Integration tests for Job Application ingestion from classified emails.

Tests the end-to-end seam: Gmail message -> confident classification ->
JobApplication creation. Verifies idempotency, source derivation,
provider failure handling, and that no Candidate is created.

**Validates: Requirements for Issue #183**
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.application.classification_service import ClassificationService
from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.gmail.infrastructure.config import GmailSettings
from src.modules.recruitment.application.job_application_service import (
    JobApplicationService,
)
from src.modules.recruitment.domain.entities import JobApplication
from src.modules.recruitment.domain.enums import ApplicationSource, JobApplicationStatus
from src.modules.recruitment.infrastructure.repositories import (
    JobApplicationRepository,
)


def _make_mock_email(
    email_id: str | None = None,
    thread_id: str | None = None,
    sender_email: str = "candidate@example.com",
    sender_name: str = "Nguyen Van A",
    has_attachments: bool = False,
) -> MagicMock:
    """Create a mock EmailMessage with realistic attributes."""
    email = MagicMock()
    email.id = uuid4()
    email.gmail_message_id = email_id or f"msg_{uuid4().hex[:12]}"
    email.gmail_thread_id = thread_id or f"thread_{uuid4().hex[:12]}"
    email.subject = "Application for Python Developer"
    email.sender_email = sender_email
    email.sender_name = sender_name
    email.snippet = "Please find my CV attached. Thank you."
    email.has_attachments = has_attachments
    email.processing_status = "unprocessed"
    email.category = None
    email.user_id = uuid4()
    return email


def _make_high_confidence_recruitment_result(
    signals: list[str] | None = None,
) -> ClassificationResult:
    """High confidence recruitment classification (above all thresholds)."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.90,
        source="ai",
        matched_signals=signals or ["subject:ứng tuyển", "sender_domain:example.com"],
    )


def _make_confident_non_recruitment_result() -> ClassificationResult:
    """Confident non-recruitment classification (e.g., vendor)."""
    return ClassificationResult(
        category=EmailCategory.vendor,
        confidence=0.90,
        source="ai",
        matched_signals=["subject:báo giá"],
    )


def _make_low_confidence_recruitment_result() -> ClassificationResult:
    """Low confidence recruitment (below needs_review threshold)."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.40,
        source="ai",
        matched_signals=["subject:CV"],
    )


@pytest.fixture
def settings() -> GmailSettings:
    """GmailSettings with standard thresholds."""
    return GmailSettings(
        classification_batch_concurrency=3,
        classification_confidence_threshold=0.75,
        classification_needs_review_threshold=0.5,
    )


@pytest.fixture
def session() -> AsyncMock:
    """Mocked AsyncSession."""
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.flush = AsyncMock()
    return mock


@pytest.fixture
def audit_logger() -> AsyncMock:
    """Mocked AuditLogger."""
    mock = AsyncMock()
    mock.log_operation = AsyncMock()
    return mock


@pytest.fixture
def email_repo() -> AsyncMock:
    """Mocked EmailRepository."""
    mock = AsyncMock()
    mock.session = MagicMock()
    mock.session.execute = AsyncMock()
    return mock


class TestJobApplicationIngestion:
    """Tests for Job Application ingestion from classified emails."""

    async def test_confident_recruitment_creates_job_application(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Confident recruitment classification creates exactly one Job Application.

        A high-confidence recruitment email should trigger the callback
        which creates a JobApplication record with source=direct,
        applicant identity copied from sender, status=new.
        """
        job_app_repo = MagicMock(spec=JobApplicationRepository)
        job_app_repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        job_app_repo.list_by_gmail_thread_id = AsyncMock(return_value=[])
        job_app_repo.create = AsyncMock()

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_high_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_high_confidence_recruitment_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
        )

        email = _make_mock_email(sender_name="Nguyen Van A", sender_email="candidate@example.com")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "classified"
        assert email.category == "recruitment"

        # Verify JobApplication was created
        job_app_repo.create.assert_awaited_once()
        created = job_app_repo.create.call_args[0][0]
        assert isinstance(created, JobApplication)
        assert created.source_email_message_id == email.id
        assert created.gmail_message_id == email.gmail_message_id
        assert created.gmail_thread_id == email.gmail_thread_id
        assert created.source == ApplicationSource.DIRECT
        assert created.applicant_name == "Nguyen Van A"
        assert created.applicant_email == "candidate@example.com"
        assert created.sender_name == "Nguyen Van A"
        assert created.sender_email == "candidate@example.com"
        assert created.job_opening_id is None
        assert created.status == JobApplicationStatus.NEW

    async def test_idempotent_same_email_does_not_create_duplicate(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Classifying the same email twice produces exactly one JobApplication.

        If a JobApplication already exists for the gmail_message_id,
        the idempotent check returns the existing record without creating
        a duplicate.
        """
        existing_app = JobApplication(
            source_email_message_id=uuid4(),
            gmail_message_id="msg_dup_check",
            gmail_thread_id="thread_dup_check",
            source=ApplicationSource.DIRECT,
            applicant_name="Nguyen Van A",
            applicant_email="candidate@example.com",
            sender_name="Nguyen Van A",
            sender_email="candidate@example.com",
        )

        job_app_repo = MagicMock(spec=JobApplicationRepository)
        job_app_repo.get_by_gmail_message_id = AsyncMock(return_value=existing_app)
        job_app_repo.create = AsyncMock()

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_high_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_high_confidence_recruitment_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
        )

        email = _make_mock_email("msg_dup_check")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        job_app_repo.create.assert_not_awaited()  # No duplicate created

    async def test_non_recruitment_email_does_not_create_application(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Non-recruitment confidently classified emails skip Job Application creation.

        Only emails classified as recruitment trigger the callback.
        Vendor, internal, and other categories should not create applications.
        """
        job_app_repo = MagicMock(spec=JobApplicationRepository)
        job_app_repo.get_by_gmail_message_id = AsyncMock()
        job_app_repo.create = AsyncMock()

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=_make_confident_non_recruitment_result())
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_confident_non_recruitment_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
        )

        email = _make_mock_email("msg_vendor")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "classified"
        assert email.category == "vendor"
        # No JobApplication created for non-recruitment
        job_app_repo.create.assert_not_awaited()

    async def test_low_confidence_does_not_create_application(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Low confidence recruitment emails are queued for review, not ingested.

        When confidence is below needs_review_threshold, the email is marked
        needs_review and no JobApplication is created.
        """
        job_app_repo = MagicMock(spec=JobApplicationRepository)
        job_app_repo.get_by_gmail_message_id = AsyncMock()
        job_app_repo.create = AsyncMock()

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_low_confidence_recruitment_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
        )

        email = _make_mock_email("msg_low_conf")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "needs_classification"
        assert email.category == "recruitment"
        # No JobApplication created for low confidence
        job_app_repo.create.assert_not_awaited()

    async def test_callback_failure_does_not_break_classification(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """If the JobApplication callback raises, classification is preserved.

        The callback is wrapped in try/except so a failure in JobApplication
        creation never causes the email classification to be rolled back.
        """
        job_app_repo = MagicMock(spec=JobApplicationRepository)
        job_app_repo.get_by_gmail_message_id = AsyncMock(
            side_effect=RuntimeError("DB connection lost")
        )

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_high_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_high_confidence_recruitment_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
        )

        email = _make_mock_email("msg_callback_fail")
        user_id = uuid4()

        # Classification should NOT fail even though callback raises
        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 0
        assert email.processing_status == "needs_review"
        assert email.category == "recruitment"
        assert email.processing_error == "JobApplication creation failed"

    async def test_referral_source_derived_from_signals(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Employee referral signal in classification result derives source.

        When matched_signals contains 'referral', the JobApplication source
        should be 'employee_referral' and applicant fields should remain
        nullable (referring employee is the sender, not the applicant).
        """
        job_app_repo = MagicMock(spec=JobApplicationRepository)
        job_app_repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        job_app_repo.list_by_gmail_thread_id = AsyncMock(return_value=[])
        job_app_repo.create = AsyncMock()

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        result_with_referral = _make_high_confidence_recruitment_result(
            signals=["subject:giới thiệu ứng viên", "sender_domain:company.com", "referral"]
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=result_with_referral)
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=result_with_referral)

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
        )

        # Referral email: sender is an employee, not the applicant
        email = _make_mock_email(
            "msg_referral",
            sender_name="Tran Thi B",
            sender_email="hr@company.com",
        )
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        job_app_repo.create.assert_awaited_once()
        created = job_app_repo.create.call_args[0][0]
        assert created.source == ApplicationSource.EMPLOYEE_REFERRAL
        # Applicant fields remain nullable for referrals
        assert created.applicant_name is None
        assert created.applicant_email is None
        # Sender fields are preserved for HR visibility
        assert created.sender_name == "Tran Thi B"
        assert created.sender_email == "hr@company.com"

    async def test_agency_source_derived_from_signals(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Agency/headhunter signal in classification result derives source.

        When matched_signals contains 'agency' or 'headhunter', the
        JobApplication source should be 'agency' and applicant fields
        should remain nullable.
        """
        job_app_repo = MagicMock(spec=JobApplicationRepository)
        job_app_repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        job_app_repo.list_by_gmail_thread_id = AsyncMock(return_value=[])
        job_app_repo.create = AsyncMock()

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        result_with_agency = _make_high_confidence_recruitment_result(
            signals=["subject:headhunter", "agency", "ứng viên"]
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=result_with_agency)
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=result_with_agency)

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
        )

        email = _make_mock_email(
            "msg_agency",
            sender_name="Recruiter from Agency",
            sender_email="recruiter@agency.com",
        )
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        job_app_repo.create.assert_awaited_once()
        created = job_app_repo.create.call_args[0][0]
        assert created.source == ApplicationSource.AGENCY
        assert created.applicant_name is None
        assert created.applicant_email is None


class TestIssue185ApplicantIdentity:
    """Applicant identity remains distinct from referral or agency senders."""

    @pytest.mark.parametrize(
        ("sender_role", "expected_source"),
        [
            ("referral", ApplicationSource.EMPLOYEE_REFERRAL),
            ("agency", ApplicationSource.AGENCY),
        ],
    )
    async def test_structured_applicant_identity_is_not_replaced_by_sender(
        self,
        sender_role: str,
        expected_source: ApplicationSource,
        session: AsyncMock,
    ) -> None:
        repo = MagicMock(spec=JobApplicationRepository)
        repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        repo.list_by_gmail_thread_id = AsyncMock(return_value=[])
        repo.create = AsyncMock(side_effect=lambda application: application)

        service = JobApplicationService(session=session, job_application_repo=repo)
        email = _make_mock_email(
            sender_name="Nguoi gioi thieu",
            sender_email="sender@agency.example",
        )
        result = ClassificationResult(
            category=EmailCategory.recruitment,
            confidence=0.95,
            source="ai",
            matched_signals=["application_language", "partner_relationship"],
            source_hints=(
                ("sender_role", sender_role),
                ("applicant_name", "Nguyen Thi Ung Vien"),
                ("applicant_email", "candidate@example.com"),
            ),
        )

        created = await service.create_from_classification(email, result)

        assert created.source == expected_source
        assert created.applicant_name == "Nguyen Thi Ung Vien"
        assert created.applicant_email == "candidate@example.com"
        assert created.sender_name == "Nguoi gioi thieu"
        assert created.sender_email == "sender@agency.example"
        assert created.evidence == [
            {"signal": "application_language"},
            {"signal": "partner_relationship"},
        ]
        assert created.source_hints == [
            {"key": "sender_role", "value": sender_role},
            {"key": "applicant_name", "value": "Nguyen Thi Ung Vien"},
            {"key": "applicant_email", "value": "candidate@example.com"},
        ]

    async def test_same_thread_supplement_links_without_creating_duplicate(
        self,
        session: AsyncMock,
    ) -> None:
        existing = JobApplication(
            source_email_message_id=uuid4(),
            gmail_message_id="msg_original",
            gmail_thread_id="thread_shared",
            applicant_name="Nguyen Thi Ung Vien",
            applicant_email="candidate@example.com",
            message_references=[
                {
                    "email_message_id": str(uuid4()),
                    "gmail_message_id": "msg_original",
                    "gmail_thread_id": "thread_shared",
                    "link_type": "source",
                }
            ],
        )
        second_split_application = JobApplication(
            source_email_message_id=existing.source_email_message_id,
            gmail_message_id="msg_original",
            gmail_thread_id="thread_shared",
            applicant_name="Tran Thi Ung Vien",
            applicant_email="second@example.com",
            message_references=list(existing.message_references),
        )
        repo = MagicMock(spec=JobApplicationRepository)
        repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        repo.list_by_gmail_thread_id = AsyncMock(
            return_value=[existing, second_split_application]
        )
        repo.update = AsyncMock(side_effect=lambda application: application)
        repo.create = AsyncMock()
        service = JobApplicationService(session=session, job_application_repo=repo)
        supplement = _make_mock_email(
            email_id="msg_supplement",
            thread_id="thread_shared",
        )

        linked = await service.create_from_classification(
            supplement, _make_high_confidence_recruitment_result()
        )

        assert linked.id == existing.id
        assert [ref["gmail_message_id"] for ref in linked.message_references] == [
            "msg_original",
            "msg_supplement",
        ]
        assert linked.message_references[-1]["link_type"] == "same_thread"
        assert second_split_application.message_references[-1]["gmail_message_id"] == (
            "msg_supplement"
        )
        assert repo.update.await_count == 2
        repo.update.assert_any_await(existing)
        repo.update.assert_any_await(second_split_application)
        repo.create.assert_not_awaited()
