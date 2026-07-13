"""Tests for dead-letter queue / needs_review classification flow.

Tests:
1. Email with low confidence (below needs_review threshold) -> needs_review
2. AI failure with rules fallback success -> needs_review (low confidence)
3. High confidence email -> classified normally

**Validates: Dead-letter queue feature**
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.application.classification_service import ClassificationService
from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.gmail.infrastructure.config import GmailSettings


def _make_mock_email(email_id: str | None = None) -> MagicMock:
    """Create a mock EmailMessage with required attributes."""
    email = MagicMock()
    email.gmail_message_id = email_id or f"msg_{uuid4().hex[:12]}"
    email.subject = "Test email subject"
    email.sender_email = "test@example.com"
    email.sender_name = "Test Sender"
    email.snippet = "This is a test email snippet for classification"
    email.has_attachments = False
    email.processing_status = "unprocessed"
    email.category = None
    return email


def _make_low_confidence_rules_result() -> ClassificationResult:
    """Create a rules result with low confidence (below review threshold)."""
    return ClassificationResult(
        category=EmailCategory.uncategorized,
        confidence=0.25,
        source="rules",
        matched_signals=[],
    )


def _make_medium_confidence_rules_result() -> ClassificationResult:
    """Create a rules result with medium confidence (triggers needs_review)."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.45,
        source="rules",
        matched_signals=["subject:cv"],
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
    return AsyncMock()


class TestDeadLetterQueue:
    """Tests for dead-letter queue (needs_review) classification."""

    async def test_low_confidence_email_marked_needs_review(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Email with confidence below needs_review_threshold -> status = needs_review."""
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=_make_medium_confidence_rules_result())

        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=ClassificationResult(
                category=EmailCategory.recruitment,
                confidence=0.4,
                source="ai",
            )
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        email = _make_mock_email("msg_low_conf")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "needs_review"

    async def test_ai_failure_with_rules_fallback_marked_needs_review(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """When AI fails but rules fallback succeeds -> needs_review due to low confidence."""
        # Rules returns confidence 0.25 (below needs_review_threshold 0.5)
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=_make_low_confidence_rules_result())

        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(side_effect=Exception("AI API down"))

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        email = _make_mock_email("msg_ai_fail")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        # Fallback succeeds but low confidence -> marked needs_review
        assert classified_count == 1
        assert email.processing_status == "needs_review"

    async def test_high_confidence_classified_normally(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """High confidence email -> status = classified (not needs_review)."""
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=ClassificationResult(
                category=EmailCategory.recruitment,
                confidence=0.90,
                source="rules",
                matched_signals=["subject:ứng tuyển", "sender_domain:vietnamworks.com"],
            )
        )

        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=ClassificationResult(
                category=EmailCategory.recruitment,
                confidence=0.90,
                source="ai",
                matched_signals=["subject:ứng tuyển", "sender_domain:vietnamworks.com"],
            )
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        email = _make_mock_email("msg_high_conf")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "classified"
        assert email.category == EmailCategory.recruitment.value
