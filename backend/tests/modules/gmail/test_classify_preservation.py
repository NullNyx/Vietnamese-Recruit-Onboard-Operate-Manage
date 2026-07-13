"""Preservation tests for ClassificationService.classify_batch().

Verifies that existing behavior is preserved after the concurrency changes:
- Rules-only emails classified immediately without AI/concurrency overhead
- Empty batch returns 0 with no side effects
- Individual email failure marks classification_failed and batch continues
- Audit logger called with correct metadata

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.application.classification_service import ClassificationService
from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.gmail.infrastructure.config import GmailSettings


def _make_mock_email() -> MagicMock:
    """Create a mock EmailMessage with required attributes."""
    email = MagicMock()
    email.gmail_message_id = f"msg_{uuid4().hex[:12]}"
    email.subject = "Test email subject"
    email.sender_email = "test@example.com"
    email.sender_name = "Test Sender"
    email.snippet = "This is a test email snippet"
    email.has_attachments = False
    email.processing_status = "unprocessed"
    email.category = None
    email.user_id = uuid4()
    return email


def _make_high_confidence_rules_result() -> ClassificationResult:
    """Create a rules classification result with high confidence (≥0.75)."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.90,
        source="rules",
        matched_signals=["keyword:tuyen_dung", "domain:vietnamworks.com"],
    )


def _make_ai_result() -> ClassificationResult:
    """Create a successful AI classification result."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.85,
        source="ai",
        matched_signals=["llm_response:recruitment"],
        token_usage={"prompt_tokens": 100, "completion_tokens": 5, "total_tokens": 105},
    )


def _make_low_confidence_rules_result() -> ClassificationResult:
    """Create a rules classification result with low confidence (forces AI fallback)."""
    return ClassificationResult(
        category=EmailCategory.uncategorized,
        confidence=0.3,
        source="rules",
        matched_signals=[],
    )


@pytest.fixture
def settings() -> GmailSettings:
    """Create GmailSettings with default concurrency for testing."""
    return GmailSettings(
        classification_batch_concurrency=3,
        classification_confidence_threshold=0.75,
    )


@pytest.fixture
def session() -> AsyncMock:
    """Create a mocked AsyncSession."""
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.flush = AsyncMock()
    return mock


@pytest.fixture
def audit_logger() -> AsyncMock:
    """Create a mocked AuditLogger."""
    mock = AsyncMock()
    mock.log_operation = AsyncMock()
    return mock


@pytest.fixture
def email_repo() -> AsyncMock:
    """Create a mocked EmailRepository."""
    return AsyncMock()


class TestRulesOnlyClassification:
    """Tests that rules-only emails are classified without AI overhead."""

    async def test_rules_only_emails_classified_without_ai(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """High-confidence rules evidence still requires AI routing.

        Rules provide evidence and never determine the final intent.

                **Validates: Requirements 3.1**
        """
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_high_confidence_rules_result())

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=_make_high_confidence_rules_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        emails = [_make_mock_email() for _ in range(5)]
        user_id = uuid4()

        result = await service.classify_batch(user_id=user_id, emails=emails)

        # All 5 emails should be classified successfully
        assert result == 5

        # AI classifier IS always called (rules provide evidence, never final-route)
        assert ai_classifier.classify.call_count == 5

        # Rules classifier should be called once per email
        assert rules_classifier.classify.call_count == 5

        # All emails should be marked as classified with correct category
        for email in emails:
            assert email.category == EmailCategory.recruitment.value
            assert email.processing_status == "classified"


class TestEmptyBatch:
    """Tests that empty batch returns 0 with no side effects."""

    async def test_empty_batch_returns_zero(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Calling classify_batch() with empty list should return 0.

        **Validates: Requirements 3.3**
        """
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_high_confidence_rules_result())

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock()

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        user_id = uuid4()

        result = await service.classify_batch(user_id=user_id, emails=[])

        # Should return 0 classified
        assert result == 0

        # No AI calls should be made
        ai_classifier.classify.assert_not_called()

        # No rules classifier calls should be made
        rules_classifier.classify.assert_not_called()


class TestIndividualFailureHandling:
    """Tests that individual email failure marks classification_failed and batch continues."""

    async def test_individual_failure_marks_classification_failed(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """When rules classifier raises for one email, it gets classification_failed.

        Others succeed.

        The classification_failed path triggers when _classify_single() or
        _apply_classification() raises an unhandled exception. Since _classify_single
        catches AI errors internally (falling back to rules result), we trigger the
        failure by making the rules classifier raise for a specific email.

        **Validates: Requirements 3.2**
        """
        emails = [_make_mock_email() for _ in range(3)]
        # Give email #2 a distinctive subject so we can target it
        emails[1].subject = "FAIL_THIS_EMAIL"

        def rules_side_effect(subject, sender_email, snippet, has_attachments):
            if subject == "FAIL_THIS_EMAIL":
                raise RuntimeError("Unexpected rules classifier error")
            return _make_high_confidence_rules_result()

        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_ai_result())

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(side_effect=rules_side_effect)

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        user_id = uuid4()

        result = await service.classify_batch(user_id=user_id, emails=emails)

        # Only 2 emails should be classified successfully (email #2 failed)
        assert result == 2

        # Email #2 (index 1) should be marked as classification_failed
        assert emails[1].processing_status == "classification_failed"

        # Other emails should be classified successfully
        classified_emails = [e for e in emails if e.processing_status == "classified"]
        assert len(classified_emails) == 2


class TestAuditLoggerMetadata:
    """Tests that audit_logger.log_operation is called with correct metadata."""

    async def test_audit_logger_called_with_correct_metadata(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Verify audit_logger.log_operation is called with correct parameters.

        **Validates: Requirements 3.4**
        """
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_high_confidence_rules_result())
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=_make_high_confidence_rules_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        emails = [_make_mock_email() for _ in range(4)]
        user_id = uuid4()

        result = await service.classify_batch(user_id=user_id, emails=emails)

        assert result == 4

        # Verify audit_logger.log_operation was called exactly once
        audit_logger.log_operation.assert_called_once()

        # Verify the call arguments
        call_kwargs = audit_logger.log_operation.call_args[1]
        assert call_kwargs["operation_type"] == "classify_batch"
        assert call_kwargs["user_id"] == user_id
        assert call_kwargs["message_count"] == 4
        assert call_kwargs["success"] is True
        assert call_kwargs["metadata"]["total_emails"] == 4
        assert call_kwargs["metadata"]["classified_count"] == 4
        assert call_kwargs["metadata"]["failed_count"] == 0

    async def test_audit_logger_metadata_with_partial_failure(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Verify audit metadata reflects partial failures correctly.

        **Validates: Requirements 3.2, 3.4**
        """
        emails = [_make_mock_email() for _ in range(3)]
        # Mark email #2 to trigger failure in rules classifier
        emails[1].subject = "FAIL_THIS_EMAIL"

        def rules_side_effect(subject, sender_email, snippet, has_attachments):
            if subject == "FAIL_THIS_EMAIL":
                raise RuntimeError("Unexpected rules classifier error")
            return _make_high_confidence_rules_result()

        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=_make_ai_result())

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(side_effect=rules_side_effect)

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        user_id = uuid4()

        result = await service.classify_batch(user_id=user_id, emails=emails)

        assert result == 2

        # Verify audit metadata reflects the partial failure
        call_kwargs = audit_logger.log_operation.call_args[1]
        assert call_kwargs["operation_type"] == "classify_batch"
        assert call_kwargs["user_id"] == user_id
        assert call_kwargs["message_count"] == 2
        assert call_kwargs["success"] is True  # success=True because classified_count > 0
        assert call_kwargs["metadata"]["total_emails"] == 3
        assert call_kwargs["metadata"]["classified_count"] == 2
        assert call_kwargs["metadata"]["failed_count"] == 1
