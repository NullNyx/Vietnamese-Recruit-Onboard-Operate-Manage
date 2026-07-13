"""Application service for the Recruitment Inbox.

Owns the business logic for managing Recruitment Inbox items: listing,
viewing detail, correcting routing intent, and dismissing items.
Also provides the ``create_from_classification`` callback called by the
Gmail ClassificationService for uncertain recruitment emails.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.recruitment.domain.entities import (
    JobApplication,
    JobApplicationLinkProposal,
    RecruitmentInboxItem,
)
from src.modules.recruitment.domain.enums import (
    ApplicationSource,
    InboxStatus,
    JobApplicationStatus,
    LinkProposalStatus,
)
from src.modules.recruitment.infrastructure.repositories import (
    JobApplicationLinkProposalRepository,
    JobApplicationRepository,
    RecruitmentInboxItemRepository,
)

logger = logging.getLogger(__name__)


class RecruitmentInboxItemNotFoundError(Exception):
    """Raised when an inbox item is not found."""


class InboxItemDismissedError(Exception):
    """Raised when attempting to modify a dismissed inbox item."""


class JobApplicationNotFoundError(Exception):
    """Raised when a target Job Application is not found."""


class LinkProposalNotFoundError(Exception):
    """Raised when a cross-thread link proposal is not found."""


class InvalidLinkProposalError(Exception):
    """Raised when a link proposal violates thread or lifecycle rules."""


@dataclass(frozen=True)
class SplitApplicant:
    """Applicant identity supplied by HR when splitting a source message."""

    name: str
    email: str | None = None
    job_opening_id: UUID | None = None


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
        job_application_repo: JobApplicationRepository | None = None,
        link_proposal_repo: JobApplicationLinkProposalRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = inbox_repo
        self._job_applications = job_application_repo
        self._link_proposals = link_proposal_repo

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
            inbox_status=(
                InboxStatus.READY_FOR_REVIEW
                if classification_result.requires_hr_split
                else InboxStatus.NEEDS_CLASSIFICATION
            ),
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

    async def split_item(
        self,
        item_id: UUID,
        applicants: list[SplitApplicant],
        source: ApplicationSource,
        user_id: UUID,
    ) -> list[JobApplication]:
        """Split one source message into independently reviewable applications."""
        application_repo = self._job_applications
        if application_repo is None:
            raise RuntimeError("Job Application repository is required for split")
        if not applicants:
            raise ValueError("At least one applicant is required")

        item = await self.get_item(item_id)
        if item.dismissed:
            raise InboxItemDismissedError(f"Cannot split dismissed inbox item {item_id}")

        occurred_at = datetime.now(UTC).isoformat()
        applications: list[JobApplication] = []
        for applicant in applicants:
            application = JobApplication(
                source_email_message_id=item.source_email_message_id,
                gmail_message_id=item.gmail_message_id,
                gmail_thread_id=item.gmail_thread_id,
                source=source,
                applicant_name=applicant.name,
                applicant_email=applicant.email,
                sender_name=item.sender_name,
                sender_email=item.sender_email,
                evidence=list(item.evidence or []),
                source_hints=list(item.source_hints or []),
                message_references=[
                    {
                        "email_message_id": str(item.source_email_message_id),
                        "gmail_message_id": item.gmail_message_id,
                        "gmail_thread_id": item.gmail_thread_id,
                        "link_type": "split_source",
                    }
                ],
                audit_history=[
                    {
                        "action": "split",
                        "performed_by_user_id": str(user_id),
                        "occurred_at": occurred_at,
                    }
                ],
                job_opening_id=applicant.job_opening_id,
                status=JobApplicationStatus.NEW,
            )
            applications.append(await application_repo.create(application))

        history = list(item.correction_history or [])
        history.append(
            {
                "action": "split",
                "job_application_ids": [str(application.id) for application in applications],
                "performed_by_user_id": str(user_id),
                "occurred_at": occurred_at,
            }
        )
        item.correction_history = history
        item.inbox_status = InboxStatus.RESOLVED
        await self._repo.update(item)
        return applications

    async def propose_cross_thread_link(
        self,
        item_id: UUID,
        target_job_application_id: UUID,
        user_id: UUID,
    ) -> JobApplicationLinkProposal:
        """Create an inert proposal; cross-thread messages are never linked here."""
        application_repo = self._job_applications
        proposal_repo = self._link_proposals
        if application_repo is None or proposal_repo is None:
            raise RuntimeError("Job Application and proposal repositories are required")

        item = await self.get_item(item_id)
        if item.dismissed:
            raise InboxItemDismissedError(f"Cannot link dismissed inbox item {item_id}")
        target = await application_repo.get_by_id(target_job_application_id)
        if target is None:
            raise JobApplicationNotFoundError(
                f"Job Application {target_job_application_id} not found"
            )
        if target.gmail_thread_id == item.gmail_thread_id:
            raise InvalidLinkProposalError(
                "Messages in the same Gmail thread are linked automatically"
            )

        proposal = JobApplicationLinkProposal(
            recruitment_inbox_item_id=item.id,
            target_job_application_id=target.id,
            status=LinkProposalStatus.PENDING,
            proposed_by_user_id=user_id,
        )
        return await proposal_repo.create(proposal)

    async def resolve_link_proposal(
        self,
        proposal_id: UUID,
        decision: LinkProposalStatus,
        user_id: UUID,
    ) -> JobApplicationLinkProposal:
        """Apply or reject a pending cross-thread proposal after HR review."""
        application_repo = self._job_applications
        proposal_repo = self._link_proposals
        if application_repo is None or proposal_repo is None:
            raise RuntimeError("Job Application and proposal repositories are required")
        if decision not in (LinkProposalStatus.CONFIRMED, LinkProposalStatus.REJECTED):
            raise InvalidLinkProposalError("Decision must be confirmed or rejected")

        proposal = await proposal_repo.get_by_id(proposal_id)
        if proposal is None:
            raise LinkProposalNotFoundError(f"Link proposal {proposal_id} not found")
        if proposal.status != LinkProposalStatus.PENDING:
            raise InvalidLinkProposalError("Link proposal has already been resolved")

        item = await self.get_item(proposal.recruitment_inbox_item_id)
        target = await application_repo.get_by_id(proposal.target_job_application_id)
        if target is None:
            raise JobApplicationNotFoundError(
                f"Job Application {proposal.target_job_application_id} not found"
            )

        now = datetime.now(UTC)
        if decision == LinkProposalStatus.CONFIRMED:
            references = list(target.message_references or [])
            if not any(
                reference.get("gmail_message_id") == item.gmail_message_id
                for reference in references
            ):
                references.append(
                    {
                        "email_message_id": str(item.source_email_message_id),
                        "gmail_message_id": item.gmail_message_id,
                        "gmail_thread_id": item.gmail_thread_id,
                        "link_type": "hr_confirmed_cross_thread",
                    }
                )
                target.message_references = references
                history = list(target.audit_history or [])
                history.append(
                    {
                        "action": "cross_thread_link_confirmed",
                        "performed_by_user_id": str(user_id),
                        "occurred_at": now.isoformat(),
                    }
                )
                target.audit_history = history
                await application_repo.update(target)
            item.inbox_status = InboxStatus.RESOLVED
        else:
            item.inbox_status = InboxStatus.READY_FOR_REVIEW

        proposal.status = decision
        proposal.resolved_by_user_id = user_id
        proposal.resolved_at = now
        await self._repo.update(item)
        return await proposal_repo.update(proposal)

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
