"""Integration-seam tests for durable AI Automation recovery."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.application.classification_service import ClassificationService
from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.gmail.infrastructure.config import GmailSettings


def make_email() -> MagicMock:
    email = MagicMock()
    email.id = uuid4()
    email.gmail_message_id = "provider-failure"
    email.subject = "Unclear message"
    email.sender_email = "sender@example.com"
    email.sender_name = "Sender"
    email.snippet = "No deterministic recruitment signal"
    email.has_attachments = False
    email.retry_count = 0
    email.is_permanently_failed = False
    email.processing_status = "unprocessed"
    email.category = None
    return email


@pytest.mark.asyncio
async def test_provider_failure_retains_email_and_schedules_bounded_retry() -> None:
    rules = MagicMock()
    rules.classify.return_value = ClassificationResult(
        category=EmailCategory.uncategorized, confidence=0.0, source="rules"
    )
    ai = AsyncMock()
    ai.classify.side_effect = RuntimeError("connection refused")
    session = AsyncMock()
    session.add = MagicMock()
    audit = AsyncMock()
    service = ClassificationService(rules, ai, AsyncMock(), audit, GmailSettings(), session)

    email = make_email()
    assert await service.classify_batch(uuid4(), [email]) == 0

    assert email.processing_status == "ai_unavailable"
    assert email.processing_error == "AI provider unavailable; HR can retry or classify manually"
    assert email.next_retry_at is not None
    assert email.category is None
    assert email.retry_count == 1


@pytest.mark.asyncio
async def test_provider_recovery_classifies_without_retry_metadata() -> None:
    rules = MagicMock()
    rules.classify.return_value = ClassificationResult(
        category=EmailCategory.uncategorized, confidence=0.0, source="rules"
    )
    ai = AsyncMock()
    ai.classify.return_value = ClassificationResult(
        category=EmailCategory.recruitment, confidence=0.9, source="ai"
    )
    session = AsyncMock()
    session.add = MagicMock()
    audit = AsyncMock()
    service = ClassificationService(rules, ai, AsyncMock(), audit, GmailSettings(), session)
    email = make_email()
    email.processing_status = "ai_unavailable"
    email.retry_count = 1
    email.processing_error = "old error"

    assert await service.classify_batch(uuid4(), [email]) == 1
    assert email.processing_status == "classified"
    assert email.category == "recruitment"
    assert email.retry_count == 0
    assert email.next_retry_at is None


@pytest.mark.asyncio
async def test_rules_path_works_when_automation_provider_is_down() -> None:
    rules = MagicMock()
    rules.classify.return_value = ClassificationResult(
        category=EmailCategory.recruitment, confidence=0.9, source="rules"
    )
    ai = AsyncMock()
    session = AsyncMock()
    session.add = MagicMock()
    audit = AsyncMock()
    service = ClassificationService(rules, ai, AsyncMock(), audit, GmailSettings(), session)
    email = make_email()

    assert await service.classify_batch(uuid4(), [email]) == 1
    ai.classify.assert_not_called()
    assert email.processing_status == "classified"
