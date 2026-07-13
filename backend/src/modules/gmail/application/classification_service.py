"""Email Classification Service for the Gmail module.

Orchestrates automatic email categorization after sync using a two-tier
approach: rule-based pre-filter for obvious patterns, then LLM fallback
for ambiguous emails. Designed for Vietnamese HR context.

Flow:
1. Email synced → processing_status = "unprocessed"
2. ClassificationService.classify_batch() called
3. Rule-based classifier handles ~60% of emails (free, <10ms)
4. LLM classifier handles remaining ~40% (Gemma 4, ~1-2s)
5. Category assigned → Gmail label applied → processing_status = "classified"
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.config import GmailSettings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.gmail.application.rules_classifier import RulesClassifier
    from src.modules.gmail.domain.entities import EmailMessage
    from src.modules.gmail.infrastructure.ai_classifier import (
        AIClassifier,
        ClassificationResult,
    )
    from src.modules.gmail.infrastructure.audit_logger import AuditLogger
    from src.modules.gmail.infrastructure.email_repository import EmailRepository
    from src.modules.recruitment.domain.entities import JobApplication

logger = logging.getLogger(__name__)

_MAX_PROVIDER_RETRIES = 3
_RETRY_BACKOFF_SECONDS = (60, 300, 900)


class AIUnavailableError(RuntimeError):
    """Raised when AI Automation cannot reach its provider."""


class ClassificationService:
    """Orchestrates email classification using rules + AI fallback.

    Processes unclassified emails in batches. For each email:
    1. Try rule-based classification (fast, free)
    2. If rules return low confidence → call AI classifier
    3. Update email category in DB
    4. Optionally apply Gmail label

    Args:
        rules_classifier: Rule-based pre-filter for obvious patterns.
        ai_classifier: LLM-based classifier for ambiguous emails.
        email_repo: Repository for email message persistence.
        audit_logger: Audit logger for tracking classification operations.
        settings: Gmail module configuration.
        session: Async database session.
    """

    def __init__(
        self,
        rules_classifier: RulesClassifier,
        ai_classifier: AIClassifier,
        email_repo: EmailRepository,
        audit_logger: AuditLogger,
        settings: GmailSettings,
        session: AsyncSession,
        on_application_created: Callable[
            [EmailMessage, ClassificationResult], Awaitable[JobApplication]
        ]
        | None = None,  # noqa: E501
    ) -> None:
        self._rules = rules_classifier
        self._ai = ai_classifier
        self._email_repo = email_repo
        self._on_application_created = on_application_created
        self._audit_logger = audit_logger
        self._settings = settings
        self._session = session

    async def classify_batch(
        self,
        user_id: UUID,
        emails: list[EmailMessage],
    ) -> int:
        """Classify a batch of unprocessed emails.

        Processes each email through the two-tier classification pipeline.
        Failures for individual emails are logged but do not stop the batch.

        Args:
            user_id: The UUID of the user who owns the emails.
            emails: List of EmailMessage entities to classify.

        Returns:
            Number of emails successfully classified.
        """
        sem = asyncio.Semaphore(self._settings.classification_batch_concurrency)

        async def _classify_one(email: EmailMessage) -> int:
            """Classify a single email under semaphore control.

            Returns 1 on success, 0 on failure.
            """
            async with sem:
                try:
                    result = await self._classify_single(email)
                    callback_ok = await self._apply_classification(email, result)
                    # Count as classified only if the result is valid AND callback succeeded
                    return 1 if (result.source != "ai_unavailable" and callback_ok) else 0
                except Exception as exc:
                    logger.error(
                        "Classification failed for email %s: %s",
                        email.gmail_message_id,
                        exc,
                        extra={"gmail_message_id": email.gmail_message_id},
                    )
                    # Mark as classification_failed for manual review
                    email.processing_status = "classification_failed"
                    self._session.add(email)
                    return 0

        results = await asyncio.gather(*[_classify_one(email) for email in emails])
        classified_count = sum(results)

        await self._session.flush()

        # Audit log the batch operation
        await self._audit_logger.log_operation(
            operation_type="classify_batch",
            user_id=user_id,
            message_count=classified_count,
            success=classified_count > 0,
            metadata={
                "total_emails": len(emails),
                "classified_count": classified_count,
                "failed_count": len(emails) - classified_count,
            },
        )

        return classified_count

    async def classify_single_email(
        self,
        user_id: UUID,
        email: EmailMessage,
    ) -> EmailCategory:
        """Classify a single email and persist the result.

        Convenience method for on-demand classification (e.g., reclassify).

        Args:
            user_id: The UUID of the user who owns the email.
            email: The EmailMessage entity to classify.

        Returns:
            The assigned EmailCategory.
        """
        result = await self._classify_single(email)
        await self._apply_classification(email, result)
        await self._session.flush()
        return result.category

    async def _classify_single(self, email: EmailMessage) -> ClassificationResult:
        """Run the two-tier classification on a single email.

        Tier 1: Rule-based classifier (keywords, sender domain, attachments) -
        provides evidence only, never final-routes.
        Tier 2: AI classifier (LLM) - always invoked.
        Rule matched_signals are merged as evidence into the AI result.

        Args:
            email: The EmailMessage entity to classify.

        Returns:
            ClassificationResult with category and confidence. Source is
            always "ai" (or "ai_unavailable"/"fallback" on AI failure).
        """
        from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult

        start_time = time.monotonic()

        # Tier 1: Rule-based classification (evidence only, never final-routes)
        rules_result = self._rules.classify(
            subject=email.subject,
            sender_email=email.sender_email,
            snippet=email.snippet,
            has_attachments=email.has_attachments,
        )

        # Always invoke AI classifier (rules never determine final routing)
        try:
            ai_result = await self._ai.classify(
                subject=email.subject,
                sender_email=email.sender_email,
                sender_name=email.sender_name,
                snippet=email.snippet,
                has_attachments=email.has_attachments,
            )
        except Exception as exc:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            raw_retry_count = getattr(email, "retry_count", 0)
            if not isinstance(raw_retry_count, int):
                return ClassificationResult(
                    category=EmailCategory.uncategorized,
                    confidence=0.0,
                    source="fallback",
                )
            retry_count = raw_retry_count
            email.processing_status = (
                "ai_unavailable" if retry_count < _MAX_PROVIDER_RETRIES else "permanently_failed"
            )
            email.processing_error = "AI provider unavailable; HR can retry or classify manually"
            email.last_retry_at = datetime.now(UTC)
            if retry_count < _MAX_PROVIDER_RETRIES:
                delay = _RETRY_BACKOFF_SECONDS[retry_count]
                email.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)
            else:
                email.next_retry_at = None
                email.is_permanently_failed = True
            email.retry_count += 1
            self._session.add(email)
            logger.warning(
                "AI classification unavailable for email %s (%dms): %s",
                email.gmail_message_id,
                latency_ms,
                exc,
            )
            return ClassificationResult(
                category=EmailCategory.uncategorized,
                confidence=0.0,
                source="ai_unavailable",
            )

        # Merge rule matched_signals as evidence into AI result
        merged_signals = list(rules_result.matched_signals) + list(ai_result.matched_signals)
        latency_ms = int((time.monotonic() - start_time) * 1000)

        if rules_result.matched_signals:
            logger.info(
                "Email %s classified by AI as %s (confidence=%.2f, %dms) rules_signals=%s",
                email.gmail_message_id[:10],
                ai_result.category.value,
                ai_result.confidence,
                latency_ms,
                rules_result.matched_signals[:3],
            )
        else:
            logger.debug(
                "Email %s classified by AI as %s (confidence=%.2f, %dms)",
                email.gmail_message_id[:10],
                ai_result.category.value,
                ai_result.confidence,
                latency_ms,
            )

        return ClassificationResult(
            category=ai_result.category,
            confidence=ai_result.confidence,
            source="ai",
            matched_signals=merged_signals,
            token_usage=ai_result.token_usage,
            source_hints=ai_result.source_hints,
        )

    async def _apply_classification(
        self,
        email: EmailMessage,
        result: ClassificationResult,
    ) -> bool:
        """Persist classification result to the email record.

        Updates the email's category and processing_status fields.
        If confidence is below needs_review_threshold, marks as needs_review
        instead of classified. If the JobApplication callback fails, marks
        as needs_review with processing_error so the outcome is reviewable.

        Args:
            email: The EmailMessage entity to update.
            result: The classification result to apply.

        Returns:
            True if the email should count as classified, False if
            classification should not be counted (callback failure).
        """
        if result.source == "ai_unavailable":
            return False

        email.category = result.category.value
        email.next_retry_at = None
        email.last_retry_at = None
        email.retry_count = 0
        email.is_permanently_failed = False

        # Dead-letter queue: if confidence below threshold, mark for human review
        if result.confidence < self._settings.classification_needs_review_threshold:
            email.processing_status = "needs_review"
            email.processing_error = None
            logger.info(
                "Email %s marked needs_review (confidence=%.2f < threshold=%.2f)",
                email.gmail_message_id[:10],
                result.confidence,
                self._settings.classification_needs_review_threshold,
            )
            self._session.add(email)
            return True

        # Invoke callback BEFORE setting classified status.
        # If callback fails, the email is marked needs_review so the
        # outcome is retryable/reviewable, not silently swallowed.
        if (
            result.category == EmailCategory.recruitment
            and self._on_application_created is not None
        ):
            try:
                await self._on_application_created(email, result)
            except Exception:
                logger.exception(
                    "JobApplication callback failed for email %s, marking needs_review",
                    email.gmail_message_id[:10],
                )
                email.processing_status = "needs_review"
                email.processing_error = "JobApplication creation failed"
                self._session.add(email)
                return False

        email.processing_status = "classified"
        email.processing_error = None
        self._session.add(email)
        return True
