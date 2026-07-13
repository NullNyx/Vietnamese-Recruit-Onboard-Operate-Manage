"""Application service for the Recruitment Inbox.

Owns the business logic for managing Recruitment Inbox items: listing,
viewing detail, correcting routing intent, and dismissing items.
Also provides the ``create_from_classification`` callback called by the
Gmail ClassificationService for uncertain recruitment emails.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.recruitment.domain.entities import RecruitmentInboxItem
from src.modules.recruitment.domain.enums import InboxStatus
from src.modules.recruitment.infrastructure.repositories import (
    RecruitmentInboxItemRepository,
)

logger = logging.getLogger(__name__)


class RecruitmentInboxItemNotFoundError(Exception):
    """Raised when an inbox item is not found."""


class InboxItemDismissedError(Exception):
    """Raised when attempting to modify a dismissed inbox item."""


class InboxService:
    """Application service for the Recruitment Inbox.

    Provides operations for listing, viewing, correcting, and dismissing
    Recruitment Inbox items. Inbox items represent emails that need HR
    attention — either below confidence threshold or with exhausted retries.

    Args:
        session: The async database session.
        inbox_repo: Repository for RecruitmentInboxItem persistence.
    """

    def __init__(
        self,
        session: AsyncSession,
        inbox_repo: RecruitmentInboxItemRepository,
    ) -> None:
        self._session = session
        self._repo = inbox_repo

    async def list_inbox(
        self,
        inbox_status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RecruitmentInboxItem], int]:
        """List inbox items with optional status filter.

        By default returns all non-dismissed items. When a status filter
        is provided, returns items matching that status.

        Args:
            inbox_status: Optional inbox status filter.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            A tuple of (list of items, total count).
        """
        return await self._repo.list_by_status(
            inbox_status=inbox_status,
            dismissed=False,
            page=page,
            page_size=page_size,
        )

    async def create_from_classification(
        self,
        email: Any,
        classification_result: Any,
    ) -> RecruitmentInboxItem:
        """Create a Recruitment Inbox item from an uncertain classification.

        Idempotent: returns the existing item if one already exists for
        this Gmail message ID. Dismissed items are not recreated.

        Builds safe attachment metadata (count, names, types, sizes) from
        the email entity without persisting raw content.

        Args:
            email: The EmailMessage entity that was classified.
            classification_result: The classification result with low confidence.

        Returns:
            The created (or existing) RecruitmentInboxItem.
        """
        # Check if dismissed — if so, do not recreate
        dismissed = await self._repo.find_dismissed_by_gmail_message_id(email.gmail_message_id)
        if dismissed is not None:
            logger.info(
                "Skipping inbox item creation for dismissed gmail_message_id=%s",
                email.gmail_message_id[:10],
            )
            return dismissed

        # Idempotent check
        existing = await self._repo.get_by_gmail_message_id(email.gmail_message_id)
        if existing is not None:
            return existing

        # Build evidence from classification result
        matched_signals = getattr(classification_result, "matched_signals", None) or []
        evidence_list = [{"signal": s} for s in matched_signals]

        source_hints_list: list[dict[str, object]] = []
        raw_hints = getattr(classification_result, "source_hints", None) or ()
        for key, value in raw_hints:
            source_hints_list.append({"key": key, "value": value})

        # Determine if retry-exhausted
        is_exhausted = getattr(email, "is_permanently_failed", False) or (
            getattr(classification_result, "source", None) == "ai_unavailable"
            and getattr(email, "retry_count", 0) >= 3
        )

        # Build safe attachment metadata from email entity
        attachments_meta: list[dict[str, object]] = []
        email_attachments = getattr(email, "attachments", None) or []
        for att in email_attachments:
            entry: dict[str, object] = {}
            name = getattr(att, "filename", None) or getattr(att, "name", None)
            if name:
                entry["name"] = name
            mime = getattr(att, "mime_type", None) or getattr(att, "type", None)
            if mime:
                entry["type"] = mime
            size = getattr(att, "size", None) or getattr(att, "size_bytes", None)
            if size is not None:
                entry["size"] = size
            if entry:
                attachments_meta.append(entry)

        item = RecruitmentInboxItem(
            source_email_message_id=email.id,
            gmail_message_id=email.gmail_message_id,
            gmail_thread_id=email.gmail_thread_id,
            sender_name=getattr(email, "sender_name", "") or "",
            sender_email=getattr(email, "sender_email", "") or "",
            subject=getattr(email, "subject", "") or "",
            snippet=getattr(email, "snippet", "") or "",
            has_attachments=getattr(email, "has_attachments", False),
            attachments_metadata=attachments_meta if attachments_meta else None,
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
            prediction_intent=classification_result.category.value
            if hasattr(classification_result.category, "value")
            else str(classification_result.category),
            confidence_raw=classification_result.confidence,
            confidence_calibrated=classification_result.confidence,
            evidence=evidence_list,
            source_hints=source_hints_list,
            is_retry_exhausted=is_exhausted,
            retry_count=getattr(email, "retry_count", 0),
            processing_error=getattr(email, "processing_error", None),
        )

        created = await self._repo.create(item)
        logger.info(
            "Created RecruitmentInboxItem id=%s from gmail_message_id=%s",
            created.id,
            email.gmail_message_id[:10],
        )
        return created

    async def get_item(self, item_id: UUID) -> RecruitmentInboxItem:
        """Get a single inbox item by ID.

        Args:
            item_id: The UUID of the inbox item.

        Returns:
            The RecruitmentInboxItem entity.

        Raises:
            RecruitmentInboxItemNotFoundError: If the item does not exist.
        """
        item = await self._repo.get_by_id(item_id)
        if item is None:
            raise RecruitmentInboxItemNotFoundError(f"Recruitment Inbox item {item_id} not found")
        return item

    async def correct_intent(
        self,
        item_id: UUID,
        corrected_intent: str,
        user_id: UUID,
    ) -> RecruitmentInboxItem:
        """Correct the routing intent of an inbox item.

        Records the correction and updates the inbox status to resolved.
        The correction history is preserved for audit.

        Args:
            item_id: The UUID of the inbox item.
            corrected_intent: The corrected routing intent value.
            user_id: The UUID of the HR user performing the correction.

        Returns:
            The updated RecruitmentInboxItem.

        Raises:
            RecruitmentInboxItemNotFoundError: If the item does not exist.
            InboxItemDismissedError: If the item is already dismissed.
        """
        item = await self._repo.get_by_id(item_id)
        if item is None:
            raise RecruitmentInboxItemNotFoundError(f"Recruitment Inbox item {item_id} not found")
        if item.dismissed:
            raise InboxItemDismissedError(f"Cannot correct dismissed inbox item {item_id}")

        # Build correction history entry
        correction_entry: dict[str, object] = {
            "previous_intent": item.prediction_intent,
            "corrected_intent": corrected_intent,
            "previous_inbox_status": item.inbox_status,
            "corrected_by_user_id": str(user_id),
            "corrected_at": datetime.now(UTC).isoformat(),
        }

        history = list(item.correction_history or [])
        history.append(correction_entry)

        item.corrected_intent = corrected_intent
        item.corrected_by_user_id = user_id
        item.corrected_at = datetime.now(UTC)
        item.correction_history = history
        if corrected_intent == "job_application":
            has_profile_material = item.has_attachments or bool(item.attachments_metadata)
            item.inbox_status = (
                InboxStatus.READY_FOR_REVIEW
                if has_profile_material
                else InboxStatus.NEEDS_INFORMATION
            )
        else:
            item.inbox_status = InboxStatus.RESOLVED

        updated = await self._repo.update(item)
        logger.info(
            "Corrected inbox item %s intent to %s (user=%s)",
            item_id,
            corrected_intent,
            user_id,
        )
        return updated

    async def dismiss_item(
        self,
        item_id: UUID,
        user_id: UUID,
    ) -> RecruitmentInboxItem:
        """Dismiss an inbox item.

        Dismissed items retain their audit record and are protected from
        worker retry recreation. The inbox status is set to resolved.

        Args:
            item_id: The UUID of the inbox item.
            user_id: The UUID of the HR user dismissing the item.

        Returns:
            The updated RecruitmentInboxItem.

        Raises:
            RecruitmentInboxItemNotFoundError: If the item does not exist.
            InboxItemDismissedError: If the item is already dismissed.
        """
        item = await self._repo.get_by_id(item_id)
        if item is None:
            raise RecruitmentInboxItemNotFoundError(f"Recruitment Inbox item {item_id} not found")
        if item.dismissed:
            raise InboxItemDismissedError(f"Inbox item {item_id} is already dismissed")

        item.dismissed = True
        item.dismissed_at = datetime.now(UTC)
        item.dismissed_by_user_id = user_id
        item.inbox_status = InboxStatus.RESOLVED

        updated = await self._repo.update(item)
        logger.info(
            "Dismissed inbox item %s (user=%s)",
            item_id,
            user_id,
        )
        return updated
