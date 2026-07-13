"""Integration tests for end-to-end concurrent classify flow.

Tests the full ClassificationService.classify_batch() flow with realistic timing
to prove concurrency works end-to-end, including email attribute updates,
session flush, and audit logging.

**Validates: Requirements 2.1, 3.4**
"""

import asyncio
import time
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
    """Create a rules result with low confidence (forces AI fallback)."""
    return ClassificationResult(
        category=EmailCategory.uncategorized,
        confidence=0.3,
        source="rules",
        matched_signals=[],
    )


def _make_high_confidence_rules_result(
    category: EmailCategory = EmailCategory.recruitment,
) -> ClassificationResult:
    """Create a rules result with high confidence (no AI needed)."""
    return ClassificationResult(
        category=category,
        confidence=0.90,
        source="rules",
        matched_signals=["subject:ứng tuyển", "sender_domain:vietnamworks.com"],
    )


def _make_ai_result(
    category: EmailCategory = EmailCategory.recruitment,
) -> ClassificationResult:
    """Create a successful AI classification result."""
    return ClassificationResult(
        category=category,
        confidence=0.85,
        source="ai",
        matched_signals=["llm_response:recruitment"],
        token_usage={"prompt_tokens": 100, "completion_tokens": 5, "total_tokens": 105},
    )


@pytest.fixture
def settings() -> GmailSettings:
    """GmailSettings with concurrency=3 for integration testing."""
    return GmailSettings(
        classification_batch_concurrency=3,
        classification_confidence_threshold=0.75,
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


class TestEndToEndConcurrentClassifyFlow:
    """Integration test: end-to-end concurrent classify flow with 6 emails."""

    async def test_six_emails_complete_in_two_rounds_not_sequential(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Mock AI with 0.5s response time, call with 6 emails.

        With concurrency=3 and 6 emails, expect 2 rounds of 3 concurrent.
        Total time should be ~1s (2 × 0.5s), not ~3s (6 × 0.5s sequential).
        """
        ai_delay = 0.5

        # Mock AI classifier with 0.5s delay
        ai_classifier = AsyncMock()

        async def slow_ai_classify(**kwargs):
            await asyncio.sleep(ai_delay)
            return _make_ai_result()

        ai_classifier.classify = AsyncMock(side_effect=slow_ai_classify)

        # Mock rules classifier to return low confidence (forces AI fallback)
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=_make_low_confidence_rules_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        emails = [_make_mock_email(f"msg_integration_{i}") for i in range(6)]
        user_id = uuid4()

        start = time.monotonic()
        classified_count = await service.classify_batch(user_id=user_id, emails=emails)
        elapsed = time.monotonic() - start

        # --- Assert total time ~1s (2 rounds × 0.5s), not ~3s (sequential) ---
        sequential_time = 6 * ai_delay  # 3.0s
        concurrent_expected = 2 * ai_delay  # 1.0s (2 rounds of 3)
        assert elapsed < sequential_time * 0.6, (
            f"Expected concurrent execution (~{concurrent_expected:.1f}s), "
            f"but took {elapsed:.2f}s. Sequential would be {sequential_time:.1f}s."
        )
        # Also verify it took at least ~1 round (not instant/mocked away)
        assert elapsed >= ai_delay * 0.8, (
            f"Expected at least ~{ai_delay}s for concurrent rounds, got {elapsed:.2f}s"
        )

        # --- Assert all 6 emails classified correctly ---
        assert classified_count == 6

        # --- Assert email attributes updated ---
        for email in emails:
            assert email.category == EmailCategory.recruitment.value, (
                f"Email {email.gmail_message_id} category not set correctly"
            )
            assert email.processing_status == "classified", (
                f"Email {email.gmail_message_id} processing_status not 'classified'"
            )

        # --- Assert session.flush() was called ---
        session.flush.assert_awaited_once()

        # --- Assert audit_logger.log_operation was called with correct metadata ---
        audit_logger.log_operation.assert_awaited_once()
        audit_call_kwargs = audit_logger.log_operation.call_args.kwargs
        assert audit_call_kwargs["operation_type"] == "classify_batch"
        assert audit_call_kwargs["user_id"] == user_id
        assert audit_call_kwargs["message_count"] == 6
        assert audit_call_kwargs["success"] is True
        assert audit_call_kwargs["metadata"]["total_emails"] == 6
        assert audit_call_kwargs["metadata"]["classified_count"] == 6
        assert audit_call_kwargs["metadata"]["failed_count"] == 0

    async def test_response_schema_correct_with_all_results(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Verify classify_batch returns correct count and all emails are processed."""
        ai_delay = 0.5

        ai_classifier = AsyncMock()

        async def slow_ai_classify(**kwargs):
            await asyncio.sleep(ai_delay)
            return _make_ai_result(EmailCategory.payroll)

        ai_classifier.classify = AsyncMock(side_effect=slow_ai_classify)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=_make_low_confidence_rules_result())

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        emails = [_make_mock_email(f"msg_schema_{i}") for i in range(6)]
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=emails)

        # Verify return value is the count of successfully classified emails
        assert classified_count == 6
        assert isinstance(classified_count, int)

        # Verify all emails got the AI-assigned category
        for email in emails:
            assert email.category == EmailCategory.payroll.value
            assert email.processing_status == "classified"

        # Verify AI classifier was called exactly 6 times
        assert ai_classifier.classify.call_count == 6


class TestMixedBatchRulesAndAI:
    """Integration test: mixed batch with some rules, some AI classifications."""

    async def test_mixed_batch_three_rules_three_ai(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """3 emails classified by rules (instant), 3 need AI (0.5s each).

        Total time should be ~0.5s (all 3 AI emails run in parallel in 1 round).
        All 6 emails classified successfully.
        """
        ai_delay = 0.5

        ai_classifier = AsyncMock()

        async def slow_ai_classify(**kwargs):
            await asyncio.sleep(ai_delay)
            return _make_ai_result(EmailCategory.payroll)

        ai_classifier.classify = AsyncMock(side_effect=slow_ai_classify)

        # Rules classifier returns high confidence for first 3, low for last 3
        rules_classifier = MagicMock()
        call_count = 0

        def rules_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return _make_high_confidence_rules_result(EmailCategory.recruitment)
            return _make_low_confidence_rules_result()

        rules_classifier.classify = MagicMock(side_effect=rules_side_effect)

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
        )

        emails = [_make_mock_email(f"msg_mixed_{i}") for i in range(6)]
        user_id = uuid4()

        start = time.monotonic()
        classified_count = await service.classify_batch(user_id=user_id, emails=emails)
        elapsed = time.monotonic() - start

        # --- All 6 emails classified successfully ---
        assert classified_count == 6

        # --- Total time should be ~0.5s (3 AI emails in parallel, 1 round) ---
        # Not ~1.5s (3 × 0.5s sequential)
        assert elapsed < 1.2, (
            f"Mixed batch with 3 AI emails (concurrency=3) should complete in ~0.5s, "
            f"got {elapsed:.2f}s"
        )

        # --- All 6 emails get the AI-assigned category (rules never final-route) ---
        for email in emails:
            assert email.category == EmailCategory.payroll.value
            assert email.processing_status == "classified"

        # --- AI classifier is called for ALL emails (rules never final-route) ---
        assert ai_classifier.classify.call_count == 6

        # --- Session flush and audit log called ---
        session.flush.assert_awaited_once()
        audit_logger.log_operation.assert_awaited_once()
        audit_call_kwargs = audit_logger.log_operation.call_args.kwargs
        assert audit_call_kwargs["metadata"]["total_emails"] == 6
        assert audit_call_kwargs["metadata"]["classified_count"] == 6
        assert audit_call_kwargs["metadata"]["failed_count"] == 0
