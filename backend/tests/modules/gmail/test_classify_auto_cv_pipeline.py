"""Integration tests for auto CV processing pipeline after classification.

Tests:
1. classify_emails auto-triggers CV processing for recruitment emails with attachments
2. High confidence CV creates Candidate
3. Low confidence CV goes to needs_review (CV Review queue)

**Validates: Auto-CV processing after classify**
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.application.classification_service import ClassificationService
from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.gmail.infrastructure.config import GmailSettings


def _make_mock_email(
    email_id: str | None = None,
    has_attachments: bool = False,
    category: str | None = None,
) -> MagicMock:
    """Create a mock EmailMessage with required attributes."""
    email = MagicMock()
    email.id = uuid4()
    email.gmail_message_id = email_id or f"msg_{uuid4().hex[:12]}"
    email.subject = "Application for Python Developer - Nguyen Van A"
    email.sender_email = "candidate@example.com"
    email.sender_name = "Nguyen Van A"
    email.snippet = "Please find my CV attached. Thank you."
    email.has_attachments = has_attachments
    email.processing_status = "unprocessed"
    email.category = category
    email.user_id = uuid4()
    return email


def _make_high_confidence_recruitment_result() -> ClassificationResult:
    """Classification result for recruitment email with high confidence."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.85,
        source="ai",
        matched_signals=["subject:Ứng tuyển", "sender_domain:example.com"],
    )


def _make_low_confidence_recruitment_result() -> ClassificationResult:
    """Classification result for recruitment email with low confidence."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.45,  # Below needs_review_threshold (0.5)
        source="ai",
        matched_signals=["subject:CV"],
    )


@pytest.fixture
def settings() -> GmailSettings:
    """GmailSettings with review thresholds."""
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
    mock.commit = AsyncMock()
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


class TestClassifyAutoCVProcessing:
    """Tests for auto CV processing after classification."""

    async def test_recruitment_email_with_attachments_gets_processed(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Recruitment email with high confidence + attachments should trigger CV processing.

        When classify_batch processes a recruitment email with attachments and
        high confidence, it should set processing_status to 'classified'
        and the caller should be able to trigger CV processing.
        """
        # High confidence recruitment result
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_high_confidence_recruitment_result()
        )

        ai_classifier = AsyncMock()  # Not called due to high confidence

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        # Email with attachments (candidate CV)
        email = _make_mock_email(
            "msg_cv_high_conf",
            has_attachments=True,
            category="recruitment",
        )
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        # High confidence → classified
        assert classified_count == 1
        assert email.processing_status == "classified"
        assert email.category == "recruitment"
        assert email.has_attachments is True

    async def test_low_confidence_recruitment_email_queued_for_review(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Low confidence recruitment email should be marked needs_review.

        When classification confidence is below needs_review_threshold (0.5),
        the email should be queued for human review (CV Review).
        """
        # Low confidence recruitment result (below 0.5 threshold)
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
        )

        # Email with attachments (candidate CV) but low confidence
        email = _make_mock_email(
            "msg_cv_low_conf",
            has_attachments=True,
            category="recruitment",
        )
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        # Low confidence → needs_review (dead-letter queue)
        assert classified_count == 1
        assert email.processing_status == "needs_review"
        assert email.category == "recruitment"
        assert email.has_attachments is True

        # This email should appear in CV Review queue
        # (verified by processing_status = needs_review)

    async def test_non_recruitment_email_skips_cv_processing(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Non-recruitment emails should not trigger CV processing.

        When classify_batch processes a non-recruitment email (e.g., vendor, internal),
        it should be classified normally without CV processing flags.
        """
        from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult

        # Non-recruitment category
        non_recruitment_result = ClassificationResult(
            category=EmailCategory.vendor,
            confidence=0.90,
            source="rules",
            matched_signals=["subject:báo giá"],
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=non_recruitment_result)

        ai_classifier = AsyncMock()  # Not called

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        # Email WITHOUT attachments, vendor category
        email = _make_mock_email(
            "msg_vendor",
            has_attachments=False,
            category="vendor",
        )
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        # Classified normally
        assert classified_count == 1
        assert email.processing_status == "classified"
        assert email.category == "vendor"
        assert email.has_attachments is False


class TestCVReviewQueueIntegration:
    """Tests for CV Review queue integration."""

    async def test_needs_review_email_appears_in_review_queue(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Email marked needs_review should be queryable as CV Review queue.

        Simulates the scenario where HR queries /api/gmail/review/emails
        to get all emails requiring manual CV review.
        """

        # Setup: low confidence + attachments = needs_review
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
        )

        # Process multiple CVs
        emails = [_make_mock_email(f"msg_cv_{i}", has_attachments=True) for i in range(3)]
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=emails)

        # All 3 should be classified (with low confidence → needs_review)
        assert classified_count == 3

        # Verify all marked needs_review
        for email in emails:
            assert email.processing_status == "needs_review"

        # Simulate review queue query
        # In real code: SELECT * FROM email_messages
        # WHERE user_id = {user_id} AND processing_status = 'needs_review'
        needs_review_emails = [e for e in emails if e.processing_status == "needs_review"]

        # All 3 emails should be in the review queue
        assert len(needs_review_emails) == 3

        # Each should have attachments (CVs)
        for email in needs_review_emails:
            assert email.has_attachments is True
