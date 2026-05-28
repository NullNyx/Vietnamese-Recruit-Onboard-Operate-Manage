"""Unit tests for concurrent processing behavior in ClassificationService.classify_batch().

Validates that classify_batch() processes emails concurrently using asyncio.Semaphore,
completing faster than sequential processing, and that the semaphore correctly limits
the number of simultaneous AI classification calls.

**Validates: Requirements 2.1, 2.2**
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


def _make_low_confidence_rules_result() -> ClassificationResult:
    """Create a rules classification result with low confidence (forces AI fallback)."""
    return ClassificationResult(
        category=EmailCategory.uncategorized,
        confidence=0.3,
        source="rules",
        matched_signals=[],
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


@pytest.fixture
def settings() -> GmailSettings:
    """Create GmailSettings with concurrency=3 for testing."""
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


class TestConcurrentProcessing:
    """Tests that classify_batch() processes emails concurrently."""

    async def test_batch_completes_faster_than_sequential(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """6 emails with 0.5s AI delay should complete in ~1s (not ~3s sequential).

        With concurrency=3 and 6 emails, we expect 2 rounds of 3 concurrent calls.
        Total time should be approximately 2 × 0.5s = 1s, not 6 × 0.5s = 3s.
        """
        ai_delay = 0.5

        # Mock AI classifier with configurable delay
        ai_classifier = AsyncMock()

        async def slow_classify(**kwargs):
            await asyncio.sleep(ai_delay)
            return _make_ai_result()

        ai_classifier.classify = AsyncMock(side_effect=slow_classify)

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

        emails = [_make_mock_email() for _ in range(6)]
        user_id = uuid4()

        start = time.monotonic()
        result = await service.classify_batch(user_id=user_id, emails=emails)
        elapsed = time.monotonic() - start

        # All 6 emails should be classified
        assert result == 6

        # With concurrency=3 and 6 emails: 2 rounds × 0.5s = ~1s
        # Sequential would be 6 × 0.5s = 3s
        # Allow generous margin but prove concurrency (must be < 2s, sequential would be ~3s)
        sequential_time = 6 * ai_delay  # 3.0s
        assert elapsed < sequential_time * 0.7, (
            f"Expected concurrent execution to be significantly faster than sequential. "
            f"Elapsed: {elapsed:.2f}s, Sequential would be: {sequential_time:.2f}s"
        )

    async def test_three_emails_with_concurrency_three(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """3 emails with concurrency=3 should all run in parallel (~1 round)."""
        ai_delay = 0.5

        ai_classifier = AsyncMock()

        async def slow_classify(**kwargs):
            await asyncio.sleep(ai_delay)
            return _make_ai_result()

        ai_classifier.classify = AsyncMock(side_effect=slow_classify)

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

        emails = [_make_mock_email() for _ in range(3)]
        user_id = uuid4()

        start = time.monotonic()
        result = await service.classify_batch(user_id=user_id, emails=emails)
        elapsed = time.monotonic() - start

        assert result == 3
        # All 3 should run in parallel: ~0.5s total, not ~1.5s sequential
        assert elapsed < 1.0, (
            f"3 emails with concurrency=3 should complete in ~0.5s, got {elapsed:.2f}s"
        )


class TestSemaphoreLimitsConcurrency:
    """Tests that the semaphore correctly limits concurrent AI calls."""

    async def test_max_concurrent_calls_respects_semaphore(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Verify that at no point do more than `classification_batch_concurrency` calls run."""
        ai_delay = 0.3
        max_concurrency = settings.classification_batch_concurrency  # 3
        current_concurrent = 0
        peak_concurrent = 0
        lock = asyncio.Lock()

        ai_classifier = AsyncMock()

        async def tracked_classify(**kwargs):
            nonlocal current_concurrent, peak_concurrent
            async with lock:
                current_concurrent += 1
                peak_concurrent = max(peak_concurrent, current_concurrent)
            try:
                await asyncio.sleep(ai_delay)
                return _make_ai_result()
            finally:
                async with lock:
                    current_concurrent -= 1

        ai_classifier.classify = AsyncMock(side_effect=tracked_classify)

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

        # Use more emails than concurrency limit to ensure semaphore is tested
        emails = [_make_mock_email() for _ in range(9)]
        user_id = uuid4()

        result = await service.classify_batch(user_id=user_id, emails=emails)

        assert result == 9
        # Peak concurrent calls should never exceed the semaphore limit
        assert peak_concurrent <= max_concurrency, (
            f"Peak concurrent calls ({peak_concurrent}) exceeded semaphore limit "
            f"({max_concurrency})"
        )
        # Also verify it actually used concurrency (peak > 1)
        assert peak_concurrent > 1, (
            f"Expected concurrent execution (peak > 1), but peak was {peak_concurrent}"
        )

    async def test_concurrency_limit_of_one_is_sequential(
        self,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """With concurrency=1, emails should process one at a time."""
        settings = GmailSettings(
            classification_batch_concurrency=1,
            classification_confidence_threshold=0.75,
        )
        ai_delay = 0.2
        current_concurrent = 0
        peak_concurrent = 0
        lock = asyncio.Lock()

        ai_classifier = AsyncMock()

        async def tracked_classify(**kwargs):
            nonlocal current_concurrent, peak_concurrent
            async with lock:
                current_concurrent += 1
                peak_concurrent = max(peak_concurrent, current_concurrent)
            try:
                await asyncio.sleep(ai_delay)
                return _make_ai_result()
            finally:
                async with lock:
                    current_concurrent -= 1

        ai_classifier.classify = AsyncMock(side_effect=tracked_classify)

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

        emails = [_make_mock_email() for _ in range(4)]
        user_id = uuid4()

        start = time.monotonic()
        result = await service.classify_batch(user_id=user_id, emails=emails)
        elapsed = time.monotonic() - start

        assert result == 4
        # With concurrency=1, peak should be exactly 1
        assert peak_concurrent == 1, (
            f"With concurrency=1, peak should be 1, got {peak_concurrent}"
        )
        # Time should be approximately sequential: 4 × 0.2s = 0.8s
        assert elapsed >= 0.7, (
            f"With concurrency=1, 4 emails should take ~0.8s, got {elapsed:.2f}s"
        )
