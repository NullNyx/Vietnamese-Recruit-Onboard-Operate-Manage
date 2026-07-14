"""Operational checks for safe Job Application classifier rollout."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.application.classification_rollout import (
    BusinessPolicy,
    ClassificationRollout,
    ReleaseMetrics,
    RolloutConfig,
    RolloutMode,
    evaluate_release_gates,
)
from src.modules.gmail.application.classification_service import ClassificationService
from src.modules.gmail.domain.entities import EmailMessage
from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.gmail.infrastructure.config import GmailSettings


@pytest.mark.asyncio
async def test_shadow_compares_candidate_without_changing_production_result() -> None:
    stable = AsyncMock(
        return_value=ClassificationResult(
            category=EmailCategory.vendor,
            confidence=0.91,
            source="ai",
        )
    )
    candidate = AsyncMock(
        return_value=ClassificationResult(
            category=EmailCategory.recruitment,
            confidence=0.99,
            source="ai",
        )
    )
    record = AsyncMock()
    rollout = ClassificationRollout(
        RolloutConfig(
            mode=RolloutMode.SHADOW,
            business_policy=BusinessPolicy.RECALL_FIRST,
            policy_version="recall-first-v1",
            stable_classifier_version="classifier-v1",
            candidate_classifier_version="classifier-v2",
        ),
        record=record,
    )

    result = await rollout.classify(
        gmail_message_id="message-123",
        stable=stable,
        candidate=candidate,
        has_cv=False,
    )

    assert result.category == EmailCategory.vendor
    stable.assert_awaited_once_with()
    candidate.assert_awaited_once_with()
    event = record.await_args.args[0]
    assert event.selected_classifier_version == "classifier-v1"
    assert event.candidate_intent == EmailCategory.recruitment.value
    assert event.has_cv is False


@pytest.mark.asyncio
async def test_shadow_candidate_provider_error_keeps_stable_workflow() -> None:
    stable_result = ClassificationResult(
        category=EmailCategory.recruitment, confidence=0.9, source="ai"
    )
    record = AsyncMock()
    rollout = ClassificationRollout(
        RolloutConfig(
            mode=RolloutMode.SHADOW,
            business_policy=BusinessPolicy.RECALL_FIRST,
            policy_version="recall-first-v2",
            stable_classifier_version="classifier-v1",
            candidate_classifier_version="classifier-v2",
        ),
        record=record,
    )

    result = await rollout.classify(
        gmail_message_id="shadow-provider-error",
        stable=AsyncMock(return_value=stable_result),
        candidate=AsyncMock(side_effect=RuntimeError("provider down")),
        has_cv=False,
    )

    assert result is stable_result
    assert record.await_args.args[0].candidate_provider_error is True


@pytest.mark.asyncio
async def test_canary_provider_error_is_recorded_before_retry() -> None:
    record = AsyncMock()
    rollout = ClassificationRollout(
        RolloutConfig(
            mode=RolloutMode.CANARY,
            business_policy=BusinessPolicy.RECALL_FIRST,
            policy_version="recall-first-v2",
            stable_classifier_version="classifier-v1",
            candidate_classifier_version="classifier-v2",
            canary_percentage=100,
        ),
        record=record,
    )

    with pytest.raises(RuntimeError, match="provider down"):
        await rollout.classify(
            gmail_message_id="canary-provider-error",
            stable=AsyncMock(),
            candidate=AsyncMock(side_effect=RuntimeError("provider down")),
            has_cv=True,
        )

    assert record.await_args.args[0].candidate_provider_error is True


@pytest.mark.asyncio
async def test_canary_partition_is_stable_across_retries() -> None:
    stable = AsyncMock(
        return_value=ClassificationResult(
            category=EmailCategory.vendor, confidence=0.9, source="ai"
        )
    )
    candidate = AsyncMock(
        return_value=ClassificationResult(
            category=EmailCategory.recruitment, confidence=0.99, source="ai"
        )
    )
    rollout = ClassificationRollout(
        RolloutConfig(
            mode=RolloutMode.CANARY,
            business_policy=BusinessPolicy.RECALL_FIRST,
            policy_version="recall-first-v2",
            stable_classifier_version="classifier-v1",
            candidate_classifier_version="classifier-v2",
            canary_percentage=50,
        )
    )

    first = await rollout.classify(
        gmail_message_id="same-email-on-every-retry",
        stable=stable,
        candidate=candidate,
        has_cv=True,
    )
    second = await rollout.classify(
        gmail_message_id="same-email-on-every-retry",
        stable=stable,
        candidate=candidate,
        has_cv=True,
    )

    assert first.category == second.category
    assert stable.await_count in {0, 2}
    assert candidate.await_count in {0, 2}
    assert stable.await_count + candidate.await_count == 2


@pytest.mark.asyncio
async def test_gmail_flow_applies_stable_result_while_shadow_only_records() -> None:
    stable = MagicMock()
    stable.classify = AsyncMock(
        return_value=ClassificationResult(
            category=EmailCategory.vendor, confidence=0.9, source="ai"
        )
    )
    candidate = MagicMock()
    candidate.classify = AsyncMock(
        return_value=ClassificationResult(
            category=EmailCategory.recruitment, confidence=0.99, source="ai"
        )
    )
    rules = MagicMock()
    rules.classify.return_value = ClassificationResult(
        category=EmailCategory.uncategorized, confidence=0.1, source="rules"
    )
    record = AsyncMock()
    rollout = ClassificationRollout(
        RolloutConfig(
            mode=RolloutMode.SHADOW,
            business_policy=BusinessPolicy.RECALL_FIRST,
            policy_version="recall-first-v2",
            stable_classifier_version="classifier-v1",
            candidate_classifier_version="classifier-v2",
        ),
        record=record,
    )
    session = MagicMock()
    session.flush = AsyncMock()
    audit = MagicMock()
    audit.log_operation = AsyncMock()
    application_created = AsyncMock()
    service = ClassificationService(
        rules,
        stable,
        MagicMock(),
        audit,
        GmailSettings(),
        session,
        on_application_created=application_created,
        rollout=rollout,
        candidate_ai_classifier=candidate,
    )
    email = EmailMessage(
        user_id=uuid4(),
        gmail_message_id="gmail-shadow-seam",
        gmail_thread_id="thread-shadow-seam",
        received_at=datetime.now(UTC),
    )

    classified = await service.classify_batch(email.user_id, [email])

    assert classified == 1
    assert email.category == EmailCategory.vendor.value
    assert email.processing_status == "classified"
    application_created.assert_not_awaited()
    assert record.await_args.args[0].candidate_intent == EmailCategory.recruitment.value


def test_full_rollout_requires_every_release_gate() -> None:
    passing = evaluate_release_gates(
        ReleaseMetrics(
            job_application_recall=0.985,
            baseline_recall=0.98,
            needs_classification_rate=0.14,
            no_cv_recall=0.99,
            correction_rate=0.03,
            review_rate=0.14,
            p95_latency_ms=1200,
            provider_error_rate=0.002,
            duplicate_count=0,
        )
    )
    failing = evaluate_release_gates(
        ReleaseMetrics(
            job_application_recall=0.97,
            baseline_recall=0.98,
            needs_classification_rate=0.16,
            no_cv_recall=None,
            correction_rate=0.08,
            review_rate=0.16,
            p95_latency_ms=1500,
            provider_error_rate=0.01,
            duplicate_count=1,
        )
    )

    assert passing.allowed is True
    assert passing.failures == ()
    assert failing.allowed is False
    assert set(failing.failures) == {
        "job_application_recall_below_98_percent",
        "needs_classification_above_15_percent",
        "recall_regression",
        "no_cv_report_missing",
        "duplicates_detected",
    }


def test_operational_guardrails_block_full_rollout() -> None:
    decision = evaluate_release_gates(
        ReleaseMetrics(
            job_application_recall=0.99,
            baseline_recall=0.98,
            needs_classification_rate=0.10,
            no_cv_recall=0.99,
            correction_rate=0.02,
            review_rate=0.10,
            p95_latency_ms=2_001,
            provider_error_rate=0.011,
            duplicate_count=0,
            retry_failure_rate=0.051,
        )
    )

    assert decision.allowed is False
    assert set(decision.failures) == {
        "p95_latency_above_2000ms",
        "provider_error_rate_above_1_percent",
        "retry_failure_rate_above_5_percent",
    }
