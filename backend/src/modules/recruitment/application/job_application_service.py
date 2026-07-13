"""Application service for Job Application ingestion.

Owns the policy for creating Job Applications after confident provider
classification. This is the only entry point for persisting a Job Application
from a classified email — the Gmail ClassificationService calls into this
service after a confident (above threshold) classification of type
``recruitment``.

Key design decisions:
- Idempotent: calling ``create_from_classification`` with the same email
  produces exactly one Job Application (keyed on ``gmail_message_id``).
- No Candidate creation: this service never promotes to Candidate.
- Provider failure is handled by the caller (ClassificationService) and
  leaves the email retryable/permanently_failed — this service is only
  invoked after a successful confident classification.
- Applicant identity is derived conservatively from structured source hints.
  For direct applications, sender identity doubles as applicant identity.
  For referrals/agency, applicant fields remain nullable.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gmail.domain.entities import EmailMessage
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.recruitment.domain.entities import JobApplication
from src.modules.recruitment.domain.enums import ApplicationSource, JobApplicationStatus
from src.modules.recruitment.infrastructure.repositories import (
    JobApplicationRepository,
)

logger = logging.getLogger(__name__)


class JobApplicationCreationError(Exception):
    """Raised when Job Application creation fails unexpectedly."""


def build_job_application_ingestion(session: AsyncSession) -> JobApplicationService:
    """Build the single production ingestion boundary for a database session."""
    return JobApplicationService(
        session=session,
        job_application_repo=JobApplicationRepository(session),
    )


class JobApplicationService:
    """Application service for creating Job Applications from classified emails.

    Owns the policy for when and how a Job Application is created from an
    email that has been confidently classified as recruitment. Idempotent
    persistence keyed on Gmail message ID.

    Args:
        session: The async database session.
        job_application_repo: Repository for Job Application persistence.
    """

    def __init__(
        self,
        session: AsyncSession,
        job_application_repo: JobApplicationRepository,
    ) -> None:
        self._session = session
        self._repo = job_application_repo

    async def create_from_classification(
        self,
        email: EmailMessage,
        classification_result: ClassificationResult,
    ) -> JobApplication:
        """Create a Job Application from a confidently classified email.

        Idempotent: returns the existing Job Application if one already
        exists for this Gmail message ID.

        Args:
            email: The EmailMessage entity that was classified.
            classification_result: The confident classification result.

        Returns:
            The created (or existing) JobApplication entity.

        Raises:
            JobApplicationCreationError: If persistence fails.
        """
        # Idempotent check: one Job Application per Gmail message
        existing = await self._repo.get_by_gmail_message_id(email.gmail_message_id)
        if existing is not None:
            logger.info(
                "JobApplication already exists for gmail_message_id=%s (id=%s)",
                email.gmail_message_id[:10],
                existing.id,
            )
            return existing

        # Derive source from classification hints
        source = self._derive_source(classification_result)

        # Derive applicant identity conservatively.
        # For direct applications, sender = applicant.
        # For referral/agency, applicant fields remain nullable.
        applicant_name: str | None = None
        applicant_email: str | None = None
        if source == ApplicationSource.DIRECT:
            applicant_name = email.sender_name or None
            applicant_email = email.sender_email or None

        job_application = JobApplication(
            source_email_message_id=email.id,
            gmail_message_id=email.gmail_message_id,
            gmail_thread_id=email.gmail_thread_id,
            source=source,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            sender_name=email.sender_name or "",
            sender_email=email.sender_email or "",
            status=JobApplicationStatus.NEW,
        )

        try:
            created = await self._repo.create(job_application)
            logger.info(
                "Created JobApplication id=%s from gmail_message_id=%s source=%s",
                created.id,
                email.gmail_message_id[:10],
                source,
            )
            return created
        except Exception as exc:
            # Check for duplicate key / unique constraint violation.
            # The savepoint ensures the outer session is not tainted.
            from sqlalchemy.exc import IntegrityError

            if isinstance(exc, IntegrityError):
                # Re-read — a concurrent insert won the race
                duplicate = await self._repo.get_by_gmail_message_id(email.gmail_message_id)
                if duplicate is not None:
                    logger.info(
                        "Concurrent duplicate JobApplication for gmail_message_id=%s "
                        "(returning existing id=%s)",
                        email.gmail_message_id[:10],
                        duplicate.id,
                    )
                    return duplicate
            logger.error(
                "Failed to create JobApplication for gmail_message_id=%s: %s",
                email.gmail_message_id,
                exc,
            )
            raise JobApplicationCreationError(f"Could not create Job Application: {exc}") from exc

    @staticmethod
    def _derive_source(classification_result: ClassificationResult) -> str:
        """Derive the application source from classification result.

        Uses structured ``source_hints`` first (from provider), then
        ``matched_signals`` substring matching as fallback.

        Args:
            classification_result: The classification result from the
                Gmail classification pipeline.

        Returns:
            The ApplicationSource string value.
        """
        # Prefer structured source_hints from provider
        hints = getattr(classification_result, "source_hints", ()) or ()
        for key, value in hints:
            key_lower = key.lower()
            value_lower = value.lower()
            if "sender_role" in key_lower:
                if value_lower in ("agency", "headhunter"):
                    return ApplicationSource.AGENCY
                if value_lower == "referral":
                    return ApplicationSource.EMPLOYEE_REFERRAL
            if "contains_referral" in key_lower and value_lower == "true":
                return ApplicationSource.EMPLOYEE_REFERRAL

        # Fall back to substring matching on matched_signals
        for signal in classification_result.matched_signals:
            signal_lower = signal.lower()
            if "referral" in signal_lower:
                return ApplicationSource.EMPLOYEE_REFERRAL
            if "agency" in signal_lower or "headhunter" in signal_lower:
                return ApplicationSource.AGENCY

        return ApplicationSource.DIRECT
