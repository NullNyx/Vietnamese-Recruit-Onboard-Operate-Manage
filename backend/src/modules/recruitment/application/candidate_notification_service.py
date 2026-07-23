"""Candidate Notification Service for the Recruitment module.

Manages sending email notifications to candidates via Gmail.

Extracted from CandidateService. Uses a GmailSendProtocol for
abstracted email delivery.

Requirements: 7.5, 9.5
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.recruitment.domain.entities import Candidate
from src.modules.recruitment.domain.exceptions import (
    CandidateNotFoundError,
    GmailNotConnectedError,
)
from src.modules.recruitment.infrastructure.audit_repository import log_audit
from src.modules.recruitment.infrastructure.repositories import CandidateRepository

logger = logging.getLogger(__name__)


@runtime_checkable
class GmailSendProtocol(Protocol):
    """Protocol for sending emails via Gmail.

    Abstracts the Gmail module's send service to avoid direct imports.
    """

    async def send_email(
        self,
        user_id: UUID,
        to: str,
        subject: str,
        body_html: str,
    ) -> None:
        """Send an email to the specified recipient."""
        ...


@runtime_checkable
class GmailConnectionChecker(Protocol):
    """Protocol for checking Gmail connection status."""

    async def is_connected(self, user_id: UUID) -> bool:
        """Check if the user's Gmail is connected."""
        ...


class CandidateNotificationService:
    """Manages email notifications to candidates.

    Provides methods for sending emails to candidates via Gmail,
    with connection validation and audit logging.

    Args:
        candidate_repo: Repository for candidate persistence.
        gmail_sender: Protocol for sending emails via Gmail.
        gmail_checker: Optional protocol for checking Gmail connection.
        session: Async database session.
        user_id: Acting user UUID for audit attribution.
    """

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        gmail_sender: GmailSendProtocol | None = None,
        gmail_checker: GmailConnectionChecker | None = None,
        session: AsyncSession | None = None,
        user_id: UUID | None = None,
    ) -> None:
        self._candidate_repo = candidate_repo
        self._gmail_sender = gmail_sender
        self._gmail_checker = gmail_checker
        self._session = session
        self._user_id = user_id

    async def send_email_to_candidate(
        self,
        candidate_id: UUID,
        subject: str,
        body_html: str,
        template_name: str | None = None,
    ) -> None:
        """Send an email to a candidate via Gmail adapter.

        Validates Gmail connection, validates candidate email, sends
        the email via the Gmail adapter protocol, and logs an audit entry.

        Args:
            candidate_id: UUID of the candidate to email.
            subject: Email subject line.
            body_html: HTML body content.
            template_name: Optional template name for the email.

        Raises:
            CandidateNotFoundError: If the candidate doesn't exist.
            GmailNotConnectedError: If Gmail is not connected.
            ValueError: If the candidate's email is invalid.
        """
        candidate = await self._get_candidate_or_raise(candidate_id)

        # Validate Gmail connection
        if self._gmail_checker:
            is_connected = await self._gmail_checker.is_connected(self._user_id or UUID(int=0))
            if not is_connected:
                raise GmailNotConnectedError()
        elif self._gmail_sender is None:
            raise GmailNotConnectedError()

        # Validate candidate email
        if not candidate.email or not candidate.email.strip():
            raise ValueError(f"Candidate email is empty or invalid: '{candidate.email}'")
        email = candidate.email.strip()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError(f"Candidate email is empty or invalid: '{candidate.email}'")

        # Send email via Gmail adapter
        if self._gmail_sender is None:
            raise GmailNotConnectedError()

        await self._gmail_sender.send_email(
            user_id=self._user_id or UUID(int=0),
            to=email,
            subject=subject,
            body_html=body_html,
        )

        # Audit log
        await log_audit(
            session=self._session,
            operation_type="candidate_email_sent",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=self._user_id,
            new_value={
                "subject": subject[:100],
                "template_name": template_name,
            },
            change_summary=(f"Email sent to candidate: subject='{subject[:100]}'"),
        )

    async def _get_candidate_or_raise(self, candidate_id: UUID) -> Candidate:
        """Retrieve a candidate by ID or raise CandidateNotFoundError.

        Args:
            candidate_id: The UUID of the candidate.

        Returns:
            The Candidate entity.

        Raises:
            CandidateNotFoundError: If the candidate doesn't exist.
        """
        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise CandidateNotFoundError(f"Candidate not found: {candidate_id}")
        return candidate
