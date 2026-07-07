"""Candidate Service for the Recruitment module.

Manages Candidate CRUD operations, status transitions, list/search,
and detail retrieval with linked CV documents and presigned URLs.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9,
6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 7.1, 7.2, 7.3, 7.4, 7.5, 13.2
"""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.modules.employee.domain.entities import Employee
from src.modules.recruitment.domain.entities import Candidate, CVDocument, JobOpening
from src.modules.recruitment.domain.enums import CandidateStatus, JobOpeningStatus
from src.modules.recruitment.domain.exceptions import (
    CalendarEventCreateFailedError,
    CalendarEventUpdateFailedError,
    CalendarGrantMissingError,
    CandidateAssignmentBlockedError,
    CandidateNotFoundError,
    GmailNotConnectedError,
    InterviewerMissingEmailError,
    InterviewerNotFoundError,
    InvalidStatusTransitionError,
    JobOpeningNotFoundError,
    JobOpeningNotOpenError,
    NoInterviewToRescheduleError,
)
from src.modules.recruitment.domain.value_objects import (
    CalendarEvent,
    CalendarEventSpec,
    ParsedCV,
)
from src.modules.recruitment.infrastructure.audit_repository import log_audit
from src.modules.recruitment.infrastructure.minio_client import RecruitmentMinIOClient
from src.modules.recruitment.infrastructure.repositories import (
    CandidateRepository,
    CVDocumentRepository,
    JobOpeningRepository,
)

if TYPE_CHECKING:
    from src.modules.identity.api.schemas import GoogleTokens, GrantStatus
    from src.modules.identity.domain.entities import OAuthGrant
    from src.modules.recruitment.infrastructure.org_settings_repository import (
        OrganizationSettingsRepository,
    )

logger = logging.getLogger(__name__)

# Return type for adapter calls executed through ``_with_calendar_token``.
_CalendarResultT = TypeVar("_CalendarResultT")


# ─── State Machine Definition ──────────────────────────────────────────

VALID_TRANSITIONS: dict[str, set[str]] = {
    CandidateStatus.NEW: {
        CandidateStatus.REVIEWING,
        CandidateStatus.INTERVIEW_SCHEDULED,
        CandidateStatus.REJECTED,
        CandidateStatus.ARCHIVED,
    },
    CandidateStatus.REVIEWING: {
        CandidateStatus.INTERVIEW_SCHEDULED,
        CandidateStatus.ACCEPTED,
        CandidateStatus.REJECTED,
        CandidateStatus.ARCHIVED,
    },
    CandidateStatus.INTERVIEW_SCHEDULED: {
        CandidateStatus.ACCEPTED,
        CandidateStatus.REJECTED,
        CandidateStatus.ARCHIVED,
    },
    CandidateStatus.ACCEPTED: set(),
    CandidateStatus.REJECTED: set(),
    CandidateStatus.ARCHIVED: set(),
}


# ─── Validation ────────────────────────────────────────────────────────

# Basic email regex: must contain exactly one @ with non-empty local and domain parts
_EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+$")


class CandidateValidationError(Exception):
    """Raised when candidate field validation fails.

    Attributes:
        errors: List of validation error dicts with field and reason.
    """

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        super().__init__(f"Candidate validation failed: {errors}")


def validate_candidate_fields(parsed_cv: ParsedCV) -> list[dict[str, Any]]:
    """Validate required candidate fields from parsed CV data.

    Checks:
    - name: non-empty, ≤ 255 characters
    - email: valid format (contains @, non-empty local and domain parts), ≤ 255 chars

    Args:
        parsed_cv: The parsed CV data to validate.

    Returns:
        List of validation error dicts. Empty list means validation passed.
    """
    errors: list[dict[str, Any]] = []

    # Validate name
    name = parsed_cv.name.strip() if parsed_cv.name else ""
    if not name:
        errors.append({"field": "name", "reason": "Name is required and cannot be empty"})
    elif len(name) > 255:
        errors.append({"field": "name", "reason": "Name must not exceed 255 characters"})

    # Validate email
    email = parsed_cv.email.strip() if parsed_cv.email else ""
    if not email:
        errors.append({"field": "email", "reason": "Email is required and cannot be empty"})
    elif len(email) > 255:
        errors.append({"field": "email", "reason": "Email must not exceed 255 characters"})
    elif not _EMAIL_PATTERN.match(email):
        errors.append(
            {
                "field": "email",
                "reason": (
                    "Email must contain exactly one '@' with non-empty local and domain parts"
                ),
            }
        )

    return errors


# ─── Protocols for cross-module communication ──────────────────────────


@runtime_checkable
class GmailLabelProtocol(Protocol):
    """Protocol for applying Gmail labels to messages.

    Abstracts the Gmail module's label service to avoid direct imports.
    """

    async def add_label(
        self,
        user_id: UUID,
        message_id: str,
        label_name: str,
        access_token: str,
    ) -> None:
        """Add a label to a Gmail message."""
        ...


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


@runtime_checkable
class DomainEventPublisher(Protocol):
    """Protocol for publishing domain events."""

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a domain event."""
        ...


@runtime_checkable
class CalendarPort(Protocol):
    """Protocol for Google Calendar event operations.

    Abstracts the recruitment ``CalendarAdapter`` so the service can be
    exercised against an in-memory fake, mirroring the ``GmailSendProtocol``
    seam. Each method takes the acting HR user's OAuth ``access_token`` (with
    the ``calendar.events`` scope) and operates on the user's primary calendar.
    """

    async def create_event(self, access_token: str, spec: CalendarEventSpec) -> CalendarEvent:
        """Create a Calendar event from the given specification."""
        ...

    async def patch_event(
        self, access_token: str, event_id: str, spec: CalendarEventSpec
    ) -> CalendarEvent:
        """Patch an existing Calendar event identified by ``event_id``."""
        ...

    async def delete_event(self, access_token: str, event_id: str) -> None:
        """Delete (cancel) the Calendar event identified by ``event_id``."""
        ...


@runtime_checkable
class OAuthGrantReader(Protocol):
    """Protocol for reading a user's stored OAuth grant.

    Abstracts the identity module's ``OAuthGrantRepository`` so the
    recruitment service can read the acting HR user's granted scopes and
    encrypted access token without a hard cross-module dependency.
    """

    async def get_by_user_id(self, user_id: UUID) -> OAuthGrant | None:
        """Return the active OAuth grant for the user, or ``None``."""
        ...


@runtime_checkable
class CalendarGrantChecker(Protocol):
    """Protocol for computing grant status and refreshing Google tokens.

    Abstracts the identity module's ``OAuthService`` to compute
    ``calendar_grant_valid`` from granted scopes (R9) and to refresh an
    expired access token during the 401 retry flow.
    """

    def determine_grant_status(self, scopes: list[str]) -> GrantStatus:
        """Compute the Gmail/Calendar grant status from granted scopes."""
        ...

    async def refresh_google_token(self, user_id: UUID) -> GoogleTokens | None:
        """Refresh the user's Google access token, or ``None`` if revoked."""
        ...


@runtime_checkable
class TokenCipher(Protocol):
    """Protocol for decrypting stored OAuth tokens.

    Abstracts the identity module's ``CryptoUtils`` (AES-256-GCM) so the
    recruitment service can decrypt the stored access token before calling
    the Calendar adapter.
    """

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a stored ciphertext into plaintext."""
        ...


@dataclass
class CVDocumentDetail:
    """CV document metadata with an optional presigned download URL.

    Attributes:
        id: UUID of the CV document.
        original_filename: Original filename of the uploaded CV.
        mime_type: MIME type of the file.
        size_bytes: File size in bytes.
        uploaded_at: Timestamp when the file was uploaded.
        presigned_url: Presigned MinIO URL for direct download, or None
            if URL generation failed.
        url_error: Error message if presigned URL generation failed.
    """

    id: UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    uploaded_at: datetime
    presigned_url: str | None = None
    url_error: str | None = None


@dataclass
class CandidateDetail:
    """Full candidate detail including linked CV documents with presigned URLs.

    Attributes:
        candidate: The Candidate entity with all fields.
        cv_documents: List of CV documents with presigned download URLs.
    """

    candidate: Candidate
    cv_documents: list[CVDocumentDetail] = field(default_factory=list)


@dataclass
class PaginatedCandidates:
    """Paginated list of candidates with total count.

    Attributes:
        candidates: List of Candidate entities for the current page.
        total_count: Total number of candidates matching the query filters.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
    """

    candidates: list[Candidate]
    total_count: int
    page: int
    page_size: int


class CandidateService:
    """Manages Candidate lifecycle, list/search, and detail retrieval.

    Provides methods for creating/updating candidates from parsed CVs,
    listing candidates with filters and search, and retrieving full
    candidate details with linked CV documents and presigned URLs.

    Implements the CandidateCreator protocol from cv_processor.py,
    providing the `create_or_update_candidate` method that the CV
    processing pipeline calls after successful parsing.

    Args:
        candidate_repo: Repository for candidate persistence.
        cv_document_repo: Repository for CV document persistence.
        minio_client: MinIO client for generating presigned URLs.
        session: Async database session.
        gmail_label_service: Optional protocol-based Gmail label service.
        access_token_provider: Optional callable returning the current OAuth token.
        user_id_provider: Optional callable returning the current user UUID.
        calendar_port: Optional Calendar adapter (protocol) for event operations.
        org_settings_repo: Optional Organization settings repository (timezone).
        oauth_grant_repo: Optional OAuth grant repository for token lookup/refresh.
        oauth_service: Optional OAuth service computing grant status and refresh.
        crypto: Optional AES-256-GCM utilities for decrypting the access token.
    """

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        cv_document_repo: CVDocumentRepository,
        minio_client: RecruitmentMinIOClient,
        session: AsyncSession,
        gmail_label_service: GmailLabelProtocol | None = None,
        gmail_sender: GmailSendProtocol | None = None,
        gmail_checker: GmailConnectionChecker | None = None,
        event_publisher: DomainEventPublisher | None = None,
        access_token_provider: object | None = None,
        user_id_provider: object | None = None,
        user_id: UUID | None = None,
        calendar_port: CalendarPort | None = None,
        org_settings_repo: OrganizationSettingsRepository | None = None,
        oauth_grant_repo: OAuthGrantReader | None = None,
        oauth_service: CalendarGrantChecker | None = None,
        crypto: TokenCipher | None = None,
        job_opening_repo: JobOpeningRepository | None = None,
    ) -> None:
        self._candidate_repo = candidate_repo
        self._cv_document_repo = cv_document_repo
        self._minio_client = minio_client
        self._session = session
        self._gmail_label_service = gmail_label_service
        self._gmail_sender = gmail_sender
        self._gmail_checker = gmail_checker
        self._event_publisher = event_publisher
        self._access_token_provider = access_token_provider
        self._user_id_provider = user_id_provider
        self._user_id = user_id
        self._calendar_port = calendar_port
        self._org_settings_repo = org_settings_repo
        self._oauth_grant_repo = oauth_grant_repo
        self._oauth_service = oauth_service
        self._crypto = crypto
        self._job_opening_repo = job_opening_repo

    # ─── Create / Update (CandidateCreator protocol) ───────────────────

    async def create_or_update_candidate(
        self,
        parsed_cv: ParsedCV,
        cv_document_id: UUID,
        source_email_id: UUID | None,
        confidence_score: float,
    ) -> Candidate:
        """Create a new candidate or update an existing one by email match.

        Implements the CandidateCreator protocol. This method:
        1. Validates name and email fields
        2. Checks for existing candidate with same email (deduplication)
        3. If exists: updates data fields but preserves existing status
        4. If new: creates with status="new"
        5. Links the CV document to the candidate
        6. Stores confidence_score and parsed_cv_json
        7. Applies "HRSpace/processed" Gmail label
        8. Logs audit entry

        Args:
            parsed_cv: Structured CV data from LLM parsing.
            cv_document_id: UUID of the associated CV document.
            source_email_id: UUID of the source email message (or None).
            confidence_score: Confidence score from LLM parsing (0.0-1.0).

        Returns:
            The created or updated Candidate entity.

        Raises:
            CandidateValidationError: If name or email validation fails.
        """
        # Step 1: Validate required fields
        validation_errors = validate_candidate_fields(parsed_cv)
        if validation_errors:
            # Store validation errors on the CV document
            cv_doc = await self._cv_document_repo.get_by_id(cv_document_id)
            if cv_doc is not None:
                cv_doc.validation_errors = validation_errors
                await self._cv_document_repo.update(cv_doc)
                await self._session.commit()

            logger.warning(
                "Candidate validation failed for CV document %s: %s",
                cv_document_id,
                validation_errors,
            )
            raise CandidateValidationError(validation_errors)

        # Step 2: Check for existing candidate by email (deduplication)
        email = parsed_cv.email.strip().lower()
        existing_candidate = await self._candidate_repo.find_by_email(email)

        if existing_candidate is not None:
            # Step 3: Update existing candidate — preserve status
            candidate = await self._update_existing_candidate(
                existing_candidate, parsed_cv, confidence_score
            )
            operation = "candidate_updated"
        else:
            # Step 4: Create new candidate with status "new"
            candidate = await self._create_new_candidate(
                parsed_cv, source_email_id, confidence_score
            )
            operation = "candidate_created"

        # Step 5: Link CV document to candidate
        await self._link_cv_document(cv_document_id, candidate.id)

        # Commit all changes
        await self._session.commit()

        # Step 6: Apply Gmail label "HRSpace/processed" (best-effort)
        await self._apply_processed_label(source_email_id)

        # Step 7: Log audit entry
        await log_audit(
            session=self._session,
            operation_type=operation,
            entity_type="candidate",
            entity_id=candidate.id,
            new_value={
                "name": candidate.name,
                "email": candidate.email,
                "status": candidate.status,
                "confidence_score": confidence_score,
                "cv_document_id": str(cv_document_id),
            },
            change_summary=(
                f"Candidate {operation.replace('candidate_', '')}: "
                f"{candidate.name} ({candidate.email}), "
                f"confidence={confidence_score:.2f}"
            ),
            success=True,
        )
        await self._session.commit()

        logger.info(
            "Candidate %s: id=%s, email=%s, confidence=%.2f",
            operation,
            candidate.id,
            candidate.email,
            confidence_score,
        )

        return candidate

    # ─── List / Detail ─────────────────────────────────────────────────

    async def list_candidates(
        self,
        *,
        status: list[str] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        min_confidence: float | None = None,
        skills: list[str] | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedCandidates:
        """Retrieve a paginated list of candidates with optional filters.

        Validates pagination parameters before delegating to the repository.
        Archived candidates are excluded by default unless the status filter
        explicitly includes "archived".

        Args:
            status: Optional list of status values to filter by.
            date_from: Optional start date for created_at range filter.
            date_to: Optional end date for created_at range filter.
            min_confidence: Optional minimum confidence score filter (0.0–1.0).
            skills: Optional list of skills to filter by (OR logic, case-insensitive).
            search: Optional text to search in name, email, phone, skills
                (case-insensitive partial match).
            page: Page number (1-indexed). Must be >= 1.
            page_size: Number of items per page. Must be between 1 and 100.

        Returns:
            PaginatedCandidates with the list of candidates and total count.

        Raises:
            ValueError: If page < 1 or page_size not in range 1–100.
        """
        # Validate pagination parameters
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")

        candidates, total_count = await self._candidate_repo.list_candidates(
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_confidence=min_confidence,
            skills=skills,
            search=search,
            page=page,
            page_size=page_size,
        )

        return PaginatedCandidates(
            candidates=candidates,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    async def get_candidate(self, candidate_id: UUID) -> CandidateDetail:
        """Retrieve full candidate detail with linked CV documents and presigned URLs.

        Fetches the candidate by ID, retrieves all linked CV documents,
        and generates a presigned download URL for each document. If URL
        generation fails for a document (e.g., MinIO unavailable or file
        missing), the document is still returned with url set to None and
        an error indicator.

        Args:
            candidate_id: UUID of the candidate to retrieve.

        Returns:
            CandidateDetail with the candidate and CV documents (each with
            a presigned URL or error indicator).

        Raises:
            CandidateNotFoundError: If no candidate exists with the given ID.
        """
        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise CandidateNotFoundError(f"Candidate not found: {candidate_id}")

        # Fetch all linked CV documents
        cv_documents = await self._cv_document_repo.find_by_candidate_id(candidate_id)

        # Generate presigned URLs for each document
        cv_document_details: list[CVDocumentDetail] = []
        for doc in cv_documents:
            detail = await self._build_cv_document_detail(doc)
            cv_document_details.append(detail)

        return CandidateDetail(
            candidate=candidate,
            cv_documents=cv_document_details,
        )

    async def _build_cv_document_detail(self, doc: CVDocument) -> CVDocumentDetail:
        """Build a CVDocumentDetail with presigned URL for a single document.

        Attempts to generate a presigned URL. If generation fails (MinIO
        unavailable or file missing), returns the document metadata with
        url=None and an error indicator.

        Args:
            doc: The CVDocument entity to build detail for.

        Returns:
            CVDocumentDetail with presigned URL or error information.
        """
        presigned_url: str | None = None
        url_error: str | None = None

        if doc.file_path:
            try:
                presigned_url = await self._minio_client.generate_presigned_url(doc.file_path)
            except Exception as exc:
                logger.warning(
                    "Failed to generate presigned URL for CV document %s (path: %s): %s",
                    doc.id,
                    doc.file_path,
                    exc,
                )
                url_error = str(exc)

        return CVDocumentDetail(
            id=doc.id,
            original_filename=doc.original_filename,
            mime_type=doc.mime_type,
            size_bytes=doc.size_bytes,
            uploaded_at=doc.uploaded_at,
            presigned_url=presigned_url,
            url_error=url_error,
        )

    # ─── Private helpers for create/update ─────────────────────────────

    async def _create_new_candidate(
        self,
        parsed_cv: ParsedCV,
        source_email_id: UUID | None,
        confidence_score: float,
    ) -> Candidate:
        """Create a new Candidate entity from parsed CV data.

        Sets status to "new" and stores the complete parsed_cv_json.

        Args:
            parsed_cv: Structured CV data.
            source_email_id: UUID of the source email message.
            confidence_score: Confidence score from parsing.

        Returns:
            The newly created Candidate entity.
        """
        candidate = Candidate(
            name=parsed_cv.name.strip(),
            email=parsed_cv.email.strip().lower(),
            phone=parsed_cv.phone or "",
            skills=parsed_cv.skills or [],
            experience=[exp.model_dump() for exp in parsed_cv.experience]
            if parsed_cv.experience
            else [],
            education=[edu.model_dump() for edu in parsed_cv.education]
            if parsed_cv.education
            else [],
            summary=parsed_cv.summary or "",
            parsed_cv_json=parsed_cv.model_dump(),
            status=CandidateStatus.NEW,
            confidence_score=confidence_score,
            source_email_message_id=source_email_id,
        )

        return await self._candidate_repo.create(candidate)

    async def _update_existing_candidate(
        self,
        existing: Candidate,
        parsed_cv: ParsedCV,
        confidence_score: float,
    ) -> Candidate:
        """Update an existing Candidate with new parsed CV data.

        Preserves the existing candidate's status while updating
        all data fields with the latest parsed CV information.

        Args:
            existing: The existing Candidate entity to update.
            parsed_cv: New structured CV data.
            confidence_score: New confidence score.

        Returns:
            The updated Candidate entity.
        """
        # Update data fields — preserve status
        existing.name = parsed_cv.name.strip()
        existing.phone = parsed_cv.phone or ""
        existing.skills = parsed_cv.skills or []
        existing.experience = (
            [exp.model_dump() for exp in parsed_cv.experience] if parsed_cv.experience else []
        )
        existing.education = (
            [edu.model_dump() for edu in parsed_cv.education] if parsed_cv.education else []
        )
        existing.summary = parsed_cv.summary or ""
        existing.parsed_cv_json = parsed_cv.model_dump()
        existing.confidence_score = confidence_score
        # Status is intentionally NOT updated (Requirement 5.5)

        return await self._candidate_repo.update(existing)

    async def _link_cv_document(self, cv_document_id: UUID, candidate_id: UUID) -> None:
        """Link a CV document to a candidate by setting candidate_id.

        Args:
            cv_document_id: UUID of the CV document to link.
            candidate_id: UUID of the candidate to link to.
        """
        cv_doc = await self._cv_document_repo.get_by_id(cv_document_id)
        if cv_doc is not None:
            cv_doc.candidate_id = candidate_id
            await self._cv_document_repo.update(cv_doc)

    async def _apply_processed_label(self, source_email_id: UUID | None) -> None:
        """Apply "HRSpace/processed" Gmail label to the source email.

        This is a best-effort operation — failures are logged but do not
        block candidate creation.

        Args:
            source_email_id: UUID of the source email message, or None.
        """
        if (
            self._gmail_label_service is None
            or source_email_id is None
            or self._access_token_provider is None
            or self._user_id_provider is None
        ):
            return

        try:
            # Get access token and user_id from providers
            access_token = None
            user_id = None

            if callable(self._access_token_provider):
                access_token = await self._access_token_provider()
            if callable(self._user_id_provider):
                user_id = await self._user_id_provider()

            if access_token and user_id:
                await self._gmail_label_service.add_label(
                    user_id=user_id,
                    message_id=str(source_email_id),
                    label_name="HRSpace/processed",
                    access_token=access_token,
                )
        except Exception as exc:
            # Best-effort: log but don't block candidate creation
            logger.warning(
                "Failed to apply 'HRSpace/processed' label for email %s: %s",
                source_email_id,
                exc,
            )

    # ─── Status transition validation ──────────────────────────────────

    def _validate_transition(self, current_status: str, target_status: str, action: str) -> None:
        """Validate that a status transition is allowed by the state machine.

        Args:
            current_status: The candidate's current status.
            target_status: The desired target status.
            action: The action name being performed (for error messages).

        Raises:
            InvalidStatusTransitionError: If the transition is not allowed.
        """
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise InvalidStatusTransitionError(current_status, action)

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

    async def _get_candidate_locked_or_raise(self, candidate_id: UUID) -> Candidate:
        candidate = await self._candidate_repo.get_by_id_for_update(candidate_id)
        if candidate is None:
            raise CandidateNotFoundError(f"Candidate not found: {candidate_id}")
        return candidate

    # ─── Status transition actions ─────────────────────────────────────

    async def reject_candidate(self, candidate_id: UUID, reason: str | None = None) -> Candidate:
        """Transition candidate to rejected status.

        Validates the transition, stores the rejection reason and
        rejected_at timestamp, and logs an audit entry.

        When the Candidate has a stored ``calendar_event_id``, the interview's
        Google Calendar event is cancelled as a best-effort side-effect AFTER
        the terminal transition has committed, so a cancellation failure can
        never undo the rejection (R8.1, R8.4, R8.6, R12.3). When no event is
        stored, no Calendar call is made (R8.3).

        Args:
            candidate_id: UUID of the candidate to reject.
            reason: Optional rejection reason (max 1000 characters).

        Returns:
            The updated Candidate entity.

        Raises:
            CandidateNotFoundError: If the candidate doesn't exist.
            InvalidStatusTransitionError: If the transition is not allowed.
        """
        candidate = await self._get_candidate_or_raise(candidate_id)
        previous_status = candidate.status

        self._validate_transition(
            current_status=candidate.status,
            target_status=CandidateStatus.REJECTED,
            action="reject",
        )

        candidate.status = CandidateStatus.REJECTED
        candidate.rejection_reason = reason
        candidate.rejected_at = datetime.now(UTC)
        candidate = await self._candidate_repo.update(candidate)
        await self._session.commit()

        await log_audit(
            session=self._session,
            operation_type="candidate_rejected",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=self._user_id,
            previous_value={"status": previous_status},
            new_value={"status": CandidateStatus.REJECTED},
            change_summary=(f"Candidate rejected: {reason[:200] if reason else 'no reason'}"),
        )

        # Best-effort: cancel the interview event AFTER the terminal transition
        # has committed (R8.1, R8.4, R8.6, R12.3). A failure here cannot undo
        # the already-committed rejection.
        await self._cancel_interview_event(candidate, trigger="reject")

        return candidate

    async def accept_candidate(self, candidate_id: UUID) -> Candidate:
        """Transition candidate to accepted status.

        Only allowed from interview_scheduled or reviewing status.
        Stores accepted_at timestamp, emits domain event, and logs audit.

        Args:
            candidate_id: UUID of the candidate to accept.

        Returns:
            The updated Candidate entity.

        Raises:
            CandidateNotFoundError: If the candidate doesn't exist.
            InvalidStatusTransitionError: If the transition is not allowed.
        """
        candidate = await self._get_candidate_or_raise(candidate_id)
        previous_status = candidate.status

        self._validate_transition(
            current_status=candidate.status,
            target_status=CandidateStatus.ACCEPTED,
            action="accept",
        )

        candidate.status = CandidateStatus.ACCEPTED
        candidate.accepted_at = datetime.now(UTC)
        candidate = await self._candidate_repo.update(candidate)

        # Touch the Job Opening updated_at timestamp when candidate is accepted
        if candidate.job_opening_id is not None and self._job_opening_repo is not None:
            job_opening = await self._job_opening_repo.get_by_id(candidate.job_opening_id)
            if job_opening is not None:
                job_opening.updated_at = datetime.now(UTC)
                await self._job_opening_repo.update(job_opening)

        await self._session.commit()

        # Emit domain event for downstream modules (onboarding)
        if self._event_publisher:
            await self._event_publisher.publish(
                event_type="candidate_accepted",
                payload={
                    "candidate_id": str(candidate.id),
                    "name": candidate.name,
                    "email": candidate.email,
                },
            )

        await log_audit(
            session=self._session,
            operation_type="candidate_accepted",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=self._user_id,
            previous_value={"status": previous_status},
            new_value={
                "status": CandidateStatus.ACCEPTED,
                "job_opening_id": (
                    str(candidate.job_opening_id) if candidate.job_opening_id else None
                ),
            },
            change_summary="Candidate accepted",
        )

        return candidate

    async def archive_candidate(self, candidate_id: UUID) -> Candidate:
        """Transition candidate to archived status.

        Not allowed from accepted status. Idempotent for already-archived
        candidates (returns existing record without modification).

        When the Candidate has a stored ``calendar_event_id``, the interview's
        Google Calendar event is cancelled as a best-effort side-effect AFTER
        the terminal transition has committed, so a cancellation failure can
        never undo the archive (R8.2, R8.5, R8.6, R12.3). When no event is
        stored, no Calendar call is made (R8.3).

        Args:
            candidate_id: UUID of the candidate to archive.

        Returns:
            The updated Candidate entity.

        Raises:
            CandidateNotFoundError: If the candidate doesn't exist.
            InvalidStatusTransitionError: If the transition is not allowed
                (e.g., from accepted status).
        """
        candidate = await self._get_candidate_or_raise(candidate_id)
        previous_status = candidate.status

        # Idempotent: already archived is a no-op
        if candidate.status == CandidateStatus.ARCHIVED:
            return candidate

        self._validate_transition(
            current_status=candidate.status,
            target_status=CandidateStatus.ARCHIVED,
            action="archive",
        )

        candidate.status = CandidateStatus.ARCHIVED
        candidate.archived_at = datetime.now(UTC)
        candidate = await self._candidate_repo.update(candidate)
        await self._session.commit()

        await log_audit(
            session=self._session,
            operation_type="candidate_archived",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=self._user_id,
            previous_value={"status": previous_status},
            new_value={"status": CandidateStatus.ARCHIVED},
            change_summary=f"Candidate archived from status '{previous_status}'",
        )

        # Best-effort: cancel the interview event AFTER the terminal transition
        # has committed (R8.2, R8.5, R8.6, R12.3). A failure here cannot undo
        # the already-committed archive.
        await self._cancel_interview_event(candidate, trigger="archive")

        return candidate

    # ─── Job Opening assignment ──────────────────────────────────────────

    _ASSIGNABLE_STATUSES: frozenset[str] = frozenset(
        {
            CandidateStatus.NEW,
            CandidateStatus.REVIEWING,
            CandidateStatus.INTERVIEW_SCHEDULED,
        }
    )

    async def assign_candidate(self, candidate_id: UUID, job_opening_id: UUID) -> Candidate:
        """Assign an unassigned Candidate to an open Job Opening.

        Rules:
        - Candidate must not already be assigned to a Job Opening.
        - Candidate status must be new, reviewing, or interview_scheduled.
        - Job Opening must have status 'open'.

        Args:
            candidate_id: UUID of the Candidate to assign.
            job_opening_id: UUID of the target Job Opening.

        Returns:
            The updated Candidate entity.

        Raises:
            CandidateNotFoundError: If the Candidate does not exist.
            JobOpeningNotFoundError: If the Job Opening does not exist.
            JobOpeningNotOpenError: If the Job Opening is not in 'open' status.
            CandidateAssignmentBlockedError: If the Candidate is in a terminal status.
            InvalidStatusTransitionError: If the Candidate is already assigned.
        """
        candidate = await self._get_candidate_locked_or_raise(candidate_id)

        if candidate.job_opening_id is not None:
            raise InvalidStatusTransitionError(
                current_status=candidate.status,
                attempted_action="assign",
            )

        if candidate.status not in self._ASSIGNABLE_STATUSES:
            raise CandidateAssignmentBlockedError(
                f"Cannot assign candidate {candidate_id} with status '{candidate.status}'"
            )

        job_opening = await self._get_open_job_opening_or_raise(job_opening_id)

        candidate.job_opening_id = job_opening_id
        candidate = await self._candidate_repo.update(candidate)

        await log_audit(
            session=self._session,
            operation_type="candidate_assigned",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=self._user_id,
            previous_value={"job_opening_id": None},
            new_value={"job_opening_id": str(job_opening_id)},
            change_summary=(
                f"Candidate assigned to Job Opening '{job_opening.title}' ({job_opening_id})"
            ),
        )
        await self._session.commit()

        return candidate

    async def reassign_candidate(self, candidate_id: UUID, new_job_opening_id: UUID) -> Candidate:
        """Reassign a Candidate to a different open Job Opening.

        Rules:
        - Candidate must already be assigned to a Job Opening.
        - new_job_opening_id must differ from the current assignment.
        - Candidate status must be new, reviewing, or interview_scheduled.
        - New Job Opening must have status 'open'.

        Args:
            candidate_id: UUID of the Candidate to reassign.
            new_job_opening_id: UUID of the new Job Opening.

        Returns:
            The updated Candidate entity.

        Raises:
            CandidateNotFoundError: If the Candidate does not exist.
            JobOpeningNotFoundError: If the Job Opening does not exist.
            JobOpeningNotOpenError: If the Job Opening is not in 'open' status.
            CandidateAssignmentBlockedError: If the Candidate is in a terminal status.
            InvalidStatusTransitionError: If the Candidate is not currently assigned.
        """
        candidate = await self._get_candidate_locked_or_raise(candidate_id)

        if candidate.job_opening_id is None:
            raise InvalidStatusTransitionError(
                current_status=candidate.status,
                attempted_action="reassign",
            )

        if candidate.status not in self._ASSIGNABLE_STATUSES:
            raise CandidateAssignmentBlockedError(
                f"Cannot reassign candidate {candidate_id} with status '{candidate.status}'"
            )

        if candidate.job_opening_id == new_job_opening_id:
            return candidate

        job_opening = await self._get_open_job_opening_or_raise(new_job_opening_id)

        previous_jo_id = candidate.job_opening_id
        candidate.job_opening_id = new_job_opening_id
        candidate = await self._candidate_repo.update(candidate)

        await log_audit(
            session=self._session,
            operation_type="candidate_reassigned",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=self._user_id,
            previous_value={"job_opening_id": str(previous_jo_id)},
            new_value={"job_opening_id": str(new_job_opening_id)},
            change_summary=(
                f"Candidate reassigned from Job Opening {previous_jo_id} "
                f"to '{job_opening.title}' ({new_job_opening_id})"
            ),
        )
        await self._session.commit()

        return candidate

    async def unassign_candidate(self, candidate_id: UUID) -> Candidate:
        """Remove a Candidate's assignment to a Job Opening.

        Rules:
        - Candidate must currently be assigned to a Job Opening.
        - Candidate status must be new, reviewing, or interview_scheduled.

        Args:
            candidate_id: UUID of the Candidate to unassign.

        Returns:
            The updated Candidate entity.

        Raises:
            CandidateNotFoundError: If the Candidate does not exist.
            CandidateAssignmentBlockedError: If the Candidate is in a terminal status.
            InvalidStatusTransitionError: If the Candidate is not currently assigned.
        """
        candidate = await self._get_candidate_locked_or_raise(candidate_id)

        if candidate.job_opening_id is None:
            raise InvalidStatusTransitionError(
                current_status=candidate.status,
                attempted_action="unassign",
            )

        if candidate.status not in self._ASSIGNABLE_STATUSES:
            raise CandidateAssignmentBlockedError(
                f"Cannot unassign candidate {candidate_id} with status '{candidate.status}'"
            )

        previous_jo_id = candidate.job_opening_id
        candidate.job_opening_id = None
        candidate = await self._candidate_repo.update(candidate)

        await log_audit(
            session=self._session,
            operation_type="candidate_unassigned",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=self._user_id,
            previous_value={"job_opening_id": str(previous_jo_id)},
            new_value={"job_opening_id": None},
            change_summary=(f"Candidate unassigned from Job Opening {previous_jo_id}"),
        )
        await self._session.commit()

        return candidate

    async def _get_open_job_opening_or_raise(self, job_opening_id: UUID) -> JobOpening:
        """Retrieve a Job Opening and verify it is in 'open' status.

        Args:
            job_opening_id: UUID of the Job Opening.

        Returns:
            The JobOpening entity.

        Raises:
            JobOpeningNotFoundError: If the Job Opening does not exist.
            RuntimeError: If job_opening_repo is not configured.
            JobOpeningNotOpenError: If the Job Opening is not in 'open' status.
        """
        if self._job_opening_repo is None:
            raise RuntimeError("JobOpeningRepository is not configured")

        job_opening = await self._job_opening_repo.get_by_id(job_opening_id)
        if job_opening is None:
            raise JobOpeningNotFoundError(f"Job Opening not found: {job_opening_id}")

        if job_opening.status != JobOpeningStatus.OPEN:
            raise JobOpeningNotOpenError(job_opening_id, job_opening.status)

        return job_opening

    async def schedule_interview(
        self,
        candidate_id: UUID,
        *,
        start: datetime,
        duration_minutes: int,
        interviewer_ids: list[UUID],
        notes: str | None = None,
    ) -> Candidate:
        """Schedule an interview by creating a Google Calendar event atomically.

        Implements the synchronous, atomic scheduling contract from ADR-0008.
        The Calendar event is created on the acting HR user's calendar **before**
        the database transaction commits; only on Calendar success does the
        Candidate transition to ``interview_scheduled`` and persist the event
        reference, the scheduled start, and the applied timezone. A Calendar
        failure rolls back all database changes and leaves the Candidate
        untouched. Attendee and Meet sub-failures are non-fatal: a created event
        succeeds even without a Meet link or with some attendees dropped.

        Steps (in order):

        1. Validate the request fields (duration 15-180, 1-10 interviewers,
           future ``start``, notes <= 1000) — R1.2-R1.5.
        2. Load the Candidate and validate the transition to
           ``interview_scheduled``; no Calendar event is created on an invalid
           transition — R2.4.
        3. Assert the acting HR user's Calendar grant before any Calendar call —
           R9.
        4. Resolve interviewer Employees and their emails — R1.7, R10.
        5. Resolve the Organization timezone, compute ``end = start + duration``,
           build the attendee list, and assemble the (tz-aware) event spec —
           R2.2, R5, R6, R11.
        6. Create the Calendar event via ``_with_calendar_token`` (401 → refresh
           → retry once) before committing — R2.1.
        7. On success, persist the event reference, start, timezone, and status,
           then commit — R2.3, R4.1-R4.3.
        8. On Calendar failure, roll back, write a failure audit entry, and raise
           ``CalendarEventCreateFailedError`` — R3.1-R3.4, R12.4.
        9. Write a success audit entry recording the schedule action — R12.1.

        Args:
            candidate_id: UUID of the Candidate.
            start: Interview start datetime (tz-aware preferred; a naive value is
                interpreted in the Organization timezone).
            duration_minutes: Interview duration in minutes (15-180 inclusive).
            interviewer_ids: Interviewer Employee identifiers (1-10).
            notes: Optional interview notes (<= 1000 characters).

        Returns:
            The updated Candidate entity with the stored Calendar reference.

        Raises:
            ValueError: If a request field violates its bounds (mapped to 422).
            CandidateNotFoundError: If the candidate doesn't exist.
            InvalidStatusTransitionError: If the transition is not allowed.
            CalendarGrantMissingError: If the acting HR user's Calendar grant is
                missing or invalid.
            InterviewerNotFoundError: If any interviewer id has no Employee.
            InterviewerMissingEmailError: If a matched interviewer has no email.
            CalendarEventCreateFailedError: If the Calendar event creation fails.
        """
        if self._calendar_port is None:
            raise RuntimeError("Calendar port is not configured")
        if self._user_id is None:
            raise RuntimeError("Acting HR user id is not configured")
        calendar_port = self._calendar_port
        user_id = self._user_id

        # Step 1: validate the request fields (re-asserted for direct-call safety).
        self._validate_schedule_request(
            start=start,
            duration_minutes=duration_minutes,
            interviewer_ids=interviewer_ids,
            notes=notes,
        )

        # Step 2: load the candidate and validate the transition (R2.4). An
        # invalid transition raises here, before any Calendar call.
        candidate = await self._get_candidate_or_raise(candidate_id)
        previous_status = candidate.status
        self._validate_transition(
            current_status=candidate.status,
            target_status=CandidateStatus.INTERVIEW_SCHEDULED,
            action="schedule_interview",
        )

        # Step 3: assert the Calendar grant before any Calendar call (R9).
        await self._assert_calendar_grant(user_id)

        # Step 4: resolve interviewer Employees and their emails (R1.7, R10).
        resolved = await self._resolve_interviewers(interviewer_ids)
        interviewer_emails = [email for _, email in resolved]

        # Step 5: timezone, end, attendees, and the tz-aware event spec.
        timezone = await self._get_org_timezone()
        tz = ZoneInfo(timezone)
        start_resolved = start.replace(tzinfo=tz) if start.tzinfo is None else start.astimezone(tz)
        end_resolved = start_resolved + timedelta(minutes=duration_minutes)
        attendee_emails = self._build_attendees(candidate, interviewer_emails)
        spec = CalendarEventSpec(
            summary=f"Interview with {candidate.name}",
            description=notes,
            start=start_resolved,
            end=end_resolved,
            timezone=timezone,
            attendee_emails=tuple(attendee_emails),
            request_meet_link=True,
        )

        # Step 6: create the Calendar event BEFORE committing (R2.1). On failure
        # roll back, audit the failure, and raise (R3.1-R3.4, R12.4).
        event = await self._create_calendar_event(user_id, candidate_id, calendar_port, spec)

        # Step 7: persist the event reference, start, timezone, and status, then
        # commit (R2.3, R4.1-R4.3). Attendee/Meet sub-failures are non-fatal: the
        # event exists, so the schedule succeeds even without a Meet link (R5.3,
        # R6.2, R6.3).
        candidate = await self._persist_interview_schedule(
            candidate, event.event_id, start_resolved, timezone
        )

        # Step 9: success audit (R12.1). Audit failure never rolls back (R12.5):
        # ``log_audit`` swallows its own failures.
        await self._audit_interview_schedule(
            user_id,
            candidate,
            event.event_id,
            start_resolved,
            timezone,
            interviewer_ids,
            previous_status,
        )

        if event.meet_link is not None:
            logger.info("Interview scheduled for candidate %s with Meet link", candidate.id)

        return candidate

    async def reschedule_interview(
        self,
        candidate_id: UUID,
        *,
        start: datetime,
        duration_minutes: int,
        interviewer_ids: list[UUID],
        notes: str | None = None,
    ) -> Candidate:
        """Reschedule an interview by patching the existing Calendar event.

        Implements the reschedule contract from ADR-0008 (R7). The existing
        Google Calendar event identified by the Candidate's stored
        ``calendar_event_id`` is patched in place with the new time window; a
        new event is never created and the existing Google Meet link is
        preserved (the patch spec sets ``request_meet_link=False``). Only the
        stored scheduled ``start`` (and applied timezone) is updated on success;
        the ``calendar_event_id`` is left unchanged. A patch failure leaves the
        stored references untouched and raises ``CalendarEventUpdateFailedError``.

        Steps (in order):

        1. Load the Candidate and require an existing ``calendar_event_id``;
           when absent, raise ``NoInterviewToRescheduleError`` before any
           Calendar call — R7.5.
        2. Assert the acting HR user's Calendar grant before any Calendar call —
           R9.2, R9.3.
        3. Validate the request fields (duration 15-180, 1-10 interviewers,
           future ``start``, notes <= 1000) — R1.2-R1.5.
        4. Resolve the Organization timezone, compute ``end = start + duration``,
           resolve interviewers, build attendees, and assemble the (tz-aware)
           patch spec with ``request_meet_link=False`` so the Meet link is
           preserved — R7.2, R11.1, R11.2.
        5. Patch the EXACT existing event via ``_with_calendar_token`` (401 →
           refresh → retry once); a new event is never created — R7.1.
        6. On success, update only the stored ``start`` and timezone, leaving the
           ``calendar_event_id`` unchanged, then commit — R7.1, R7.3.
        7. On patch failure, roll back any staged change, write a failure audit
           entry, and raise ``CalendarEventUpdateFailedError`` — R7.4, R12.4.
        8. Write a reschedule audit entry recording the previous and new start —
           R12.2.

        Args:
            candidate_id: UUID of the Candidate.
            start: New interview start datetime (tz-aware preferred; a naive
                value is interpreted in the Organization timezone).
            duration_minutes: Interview duration in minutes (15-180 inclusive).
            interviewer_ids: Interviewer Employee identifiers (1-10).
            notes: Optional interview notes (<= 1000 characters).

        Returns:
            The updated Candidate entity with the new scheduled start.

        Raises:
            ValueError: If a request field violates its bounds (mapped to 422).
            CandidateNotFoundError: If the candidate doesn't exist.
            NoInterviewToRescheduleError: If the Candidate has no stored event.
            CalendarGrantMissingError: If the acting HR user's Calendar grant is
                missing or invalid.
            InterviewerNotFoundError: If any interviewer id has no Employee.
            InterviewerMissingEmailError: If a matched interviewer has no email.
            CalendarEventUpdateFailedError: If the Calendar event patch fails.
        """
        if self._calendar_port is None:
            raise RuntimeError("Calendar port is not configured")
        if self._user_id is None:
            raise RuntimeError("Acting HR user id is not configured")
        user_id = self._user_id

        # Step 1: load the Candidate and require an existing event (R7.5). When
        # absent, raise before any Calendar call.
        candidate = await self._get_candidate_or_raise(candidate_id)
        event_id = candidate.calendar_event_id
        if event_id is None:
            raise NoInterviewToRescheduleError()

        # Step 2: assert the Calendar grant before any Calendar call (R9.2, R9.3).
        await self._assert_calendar_grant(user_id)

        # Step 3: validate the request fields (re-asserted for direct-call safety).
        self._validate_schedule_request(
            start=start,
            duration_minutes=duration_minutes,
            interviewer_ids=interviewer_ids,
            notes=notes,
        )

        # Step 4: timezone, end, attendees, and the tz-aware patch spec. The patch
        # must NOT request a new Meet link so the existing one is preserved (R7.2).
        resolved = await self._resolve_interviewers(interviewer_ids)
        interviewer_emails = [email for _, email in resolved]
        timezone = await self._get_org_timezone()
        tz = ZoneInfo(timezone)
        start_resolved = start.replace(tzinfo=tz) if start.tzinfo is None else start.astimezone(tz)
        end_resolved = start_resolved + timedelta(minutes=duration_minutes)
        attendee_emails = self._build_attendees(candidate, interviewer_emails)
        spec = CalendarEventSpec(
            summary=f"Interview with {candidate.name}",
            description=notes,
            start=start_resolved,
            end=end_resolved,
            timezone=timezone,
            attendee_emails=tuple(attendee_emails),
            request_meet_link=False,
        )

        # Capture the previous start before any mutation (R12.2).
        previous_start = candidate.interview_start_at

        # Step 5: patch the EXACT existing event BEFORE committing (R7.1). On
        # failure, roll back, audit, and raise; references stay unchanged (R7.4,
        # R12.4).
        await self._patch_calendar_event(
            user_id=user_id,
            candidate_id=candidate_id,
            event_id=event_id,
            spec=spec,
        )

        # Step 6: update only the stored start and timezone, leaving the
        # calendar_event_id unchanged, then commit (R7.1, R7.3).
        candidate.interview_start_at = start_resolved
        candidate.interview_timezone = timezone
        candidate = await self._candidate_repo.update(candidate)
        await self._session.commit()

        # Step 8: reschedule audit recording previous/new start (R12.2). Audit
        # failure never rolls back (R12.5): log_audit swallows its own failures.
        previous_start_iso = previous_start.isoformat() if previous_start is not None else None
        await log_audit(
            session=self._session,
            operation_type="interview_rescheduled",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=user_id,
            previous_value={"start": previous_start_iso},
            new_value={
                "previous_start": previous_start_iso,
                "new_start": start_resolved.isoformat(),
                "calendar_event_id": event_id,
                "candidate_id": str(candidate.id),
                "timezone": timezone,
            },
            change_summary=(
                f"Interview rescheduled to {start_resolved.isoformat()}; event {event_id}"
            ),
            success=True,
        )
        await self._session.commit()

        return candidate

    def _validate_schedule_request(
        self,
        *,
        start: datetime,
        duration_minutes: int,
        interviewer_ids: list[UUID],
        notes: str | None,
    ) -> None:
        """Validate schedule/reschedule request fields (R1.2-R1.5).

        Re-asserts the request bounds in the service even though Pydantic also
        validates them at the API boundary, so direct service calls are safe.
        The future-``start`` rule (R1.4) is enforced here against the current
        time rather than as a bare Pydantic validator.

        Args:
            start: Interview start datetime; must be strictly in the future.
            duration_minutes: Must be within 15-180 inclusive.
            interviewer_ids: Must contain between 1 and 10 identifiers inclusive.
            notes: When present, must be at most 1000 characters.

        Raises:
            ValueError: If any field violates its bound. The API layer maps this
                to a 422 response.
        """
        if not 15 <= duration_minutes <= 180:
            raise ValueError("duration_minutes must be between 15 and 180 inclusive")
        if not 1 <= len(interviewer_ids) <= 10:
            raise ValueError("interviewer_ids must contain between 1 and 10 interviewers")
        if notes is not None and len(notes) > 1000:
            raise ValueError("notes must be at most 1000 characters")

        now = datetime.now(UTC)
        start_for_check = start if start.tzinfo is not None else start.replace(tzinfo=UTC)
        if start_for_check <= now:
            raise ValueError("start must be strictly in the future")

    # ─── Calendar scheduling helpers ───────────────────────────────────

    async def _patch_calendar_event(
        self,
        user_id: UUID,
        candidate_id: UUID,
        event_id: str,
        spec: CalendarEventSpec,
    ) -> None:
        """Patch an existing Calendar event, logging and rolling back on failure."""
        if self._calendar_port is None:
            raise RuntimeError("Calendar port is not configured")

        calendar_port = self._calendar_port

        try:
            await self._with_calendar_token(
                user_id,
                lambda token: calendar_port.patch_event(token, event_id, spec),
            )
        except Exception as exc:
            await self._session.rollback()
            await log_audit(
                session=self._session,
                operation_type="interview_reschedule_failed",
                entity_type="candidate",
                entity_id=candidate_id,
                user_id=user_id,
                new_value={
                    "attempted_action": "reschedule_interview",
                    "candidate_id": str(candidate_id),
                    "calendar_event_id": event_id,
                    "error": str(exc),
                },
                change_summary="Interview reschedule failed: Calendar event patch error",
                success=False,
            )
            await self._session.commit()
            raise CalendarEventUpdateFailedError() from exc

    async def _assert_calendar_grant(self, user_id: UUID) -> None:
        """Assert the acting HR user has a valid Google Calendar grant.

        Reuses ``OAuthService.determine_grant_status`` against the user's
        stored ``OAuthGrant.scopes``. Raises before any Calendar call when the
        grant is missing or ``calendar_grant_valid`` is false, directing the
        user to re-consent to Calendar access (R9).

        Args:
            user_id: The acting HR user's identifier.

        Raises:
            CalendarGrantMissingError: If no grant exists or the Calendar scope
                is not currently granted.
        """
        if self._oauth_grant_repo is None or self._oauth_service is None:
            raise RuntimeError("Calendar grant dependencies are not configured")

        grant = await self._oauth_grant_repo.get_by_user_id(user_id)
        if grant is None:
            raise CalendarGrantMissingError()

        grant_status = self._oauth_service.determine_grant_status(grant.scopes)
        if not grant_status.calendar_grant_valid:
            raise CalendarGrantMissingError()

    async def _resolve_interviewers(
        self, interviewer_ids: list[UUID]
    ) -> list[tuple[Employee, str]]:
        """Resolve interviewer identifiers to Employees with usable emails.

        Loads the Employee records for the given identifiers, then enforces
        two rules in order:

        1. Every identifier must match an existing Employee, otherwise an
           :class:`InterviewerNotFoundError` is raised listing the unmatched
           identifiers (R1.7).
        2. Every matched Employee must have a non-blank email, otherwise an
           :class:`InterviewerMissingEmailError` is raised identifying the
           first interviewer that cannot be invited (R10).

        Args:
            interviewer_ids: The interviewer Employee identifiers from the
                request (order preserved in the result).

        Returns:
            List of ``(Employee, email)`` tuples in request order, with each
            email stripped of surrounding whitespace.

        Raises:
            InterviewerNotFoundError: If any identifier has no matching Employee.
            InterviewerMissingEmailError: If a matched Employee has a blank email.
        """
        statement = select(Employee).where(col(Employee.id).in_(interviewer_ids))
        result = await self._session.execute(statement)
        employees_by_id = {employee.id: employee for employee in result.scalars().all()}

        unmatched = [id_ for id_ in interviewer_ids if id_ not in employees_by_id]
        if unmatched:
            raise InterviewerNotFoundError(unmatched)

        resolved: list[tuple[Employee, str]] = []
        for id_ in interviewer_ids:
            employee = employees_by_id[id_]
            email = (employee.email or "").strip()
            if not email:
                raise InterviewerMissingEmailError(employee.id)
            resolved.append((employee, email))
        return resolved

    async def _get_org_timezone(self) -> str:
        """Return the Organization's configured IANA timezone.

        Delegates to ``OrganizationSettingsRepository.get_timezone()``, which
        seeds the configured default on first access (R11).

        Returns:
            The IANA timezone string applied to interview events.
        """
        if self._org_settings_repo is None:
            raise RuntimeError("Organization settings repository is not configured")
        return await self._org_settings_repo.get_timezone()

    def _build_attendees(self, candidate: Candidate, interviewer_emails: list[str]) -> list[str]:
        """Build the de-duplicated attendee email list for an interview.

        Combines the Candidate's email with every interviewer email (R5.1,
        R5.2), preserving first-seen order and removing case-insensitive
        duplicates and blank entries.

        Args:
            candidate: The Candidate being interviewed.
            interviewer_emails: Interviewer Employee emails (already resolved).

        Returns:
            Ordered, de-duplicated list of attendee email addresses.
        """
        attendees: list[str] = []
        seen: set[str] = set()
        for email in [candidate.email, *interviewer_emails]:
            normalized = (email or "").strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            attendees.append(normalized)
        return attendees

    async def _cancel_interview_event(self, candidate: Candidate, *, trigger: str) -> None:
        """Best-effort cancellation of a Candidate's interview Calendar event.

        Invoked AFTER a terminal transition (reject/archive) has already
        committed, so this method never raises: a cancellation failure must not
        undo the committed transition (R8.4, R8.5). Behavior:

        - When no Calendar dependencies are configured (``calendar_port`` or the
          acting ``user_id`` is absent), do nothing — this preserves the legacy
          behavior for callers constructed without Calendar wiring.
        - When the Candidate has no stored ``calendar_event_id``, make no
          Calendar call (R8.3).
        - Otherwise delete the EXACT stored event via ``_with_calendar_token``.
          On success, write an ``interview_event_cancelled`` audit entry
          recording the acting HR user, the Candidate id, the cancelled
          ``calendar_event_id``, and the trigger (R12.3). On any failure, swallow
          the error and write an ``interview_cancel_failed`` audit entry
          (``success=False``) recording the action and the ``calendar_event_id``
          (R8.6).

        Args:
            candidate: The Candidate whose interview event should be cancelled.
            trigger: The terminal action that triggered the cancellation
                (``"reject"`` or ``"archive"``).
        """
        # No Calendar wiring → preserve legacy transition-only behavior (R8.3).
        if self._calendar_port is None or self._user_id is None:
            return

        event_id = candidate.calendar_event_id
        if event_id is None:
            # No interview event to cancel (R8.3).
            return

        calendar_port = self._calendar_port
        user_id = self._user_id

        try:
            await self._with_calendar_token(
                user_id,
                lambda token: calendar_port.delete_event(token, event_id),
            )
        except Exception as exc:
            # Cancellation failure must NOT block the already-committed terminal
            # transition (R8.4, R8.5). Record a failed-cancellation audit entry
            # capturing the action and the calendar_event_id (R8.6).
            logger.warning(
                "Calendar event cancellation failed for candidate %s (event %s) on %s: %s",
                candidate.id,
                event_id,
                trigger,
                exc,
            )
            await log_audit(
                session=self._session,
                operation_type="interview_cancel_failed",
                entity_type="candidate",
                entity_id=candidate.id,
                user_id=user_id,
                new_value={
                    "attempted_action": f"{trigger}_cancel_interview",
                    "candidate_id": str(candidate.id),
                    "calendar_event_id": event_id,
                    "trigger": trigger,
                    "success": False,
                    "error": str(exc),
                },
                change_summary=(f"Interview cancellation failed on {trigger}; event {event_id}"),
                success=False,
            )
            await self._session.commit()
            return

        # Successful cancellation audit (R12.3).
        await log_audit(
            session=self._session,
            operation_type="interview_event_cancelled",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=user_id,
            new_value={
                "candidate_id": str(candidate.id),
                "calendar_event_id": event_id,
                "trigger": trigger,
            },
            change_summary=(f"Interview event cancelled on {trigger}; event {event_id}"),
            success=True,
        )
        await self._session.commit()

    async def _with_calendar_token(
        self,
        user_id: UUID,
        fn: Callable[[str], Awaitable[_CalendarResultT]],
    ) -> _CalendarResultT:
        """Run a Calendar adapter call, refreshing the token once on 401.

        Decrypts the acting HR user's stored access token and invokes ``fn``
        with it. If the adapter raises an ``httpx`` ``401``, the token is
        refreshed via ``OAuthService``/``OAuthGrantRepository`` and ``fn`` is
        retried exactly once, mirroring the Gmail ``SendService`` pattern.

        Args:
            user_id: The acting HR user's identifier.
            fn: An async callable that performs the adapter call given a valid
                access token.

        Returns:
            The result of the adapter call.

        Raises:
            CalendarGrantMissingError: If no grant exists or the token refresh
                fails (the grant was revoked).
            httpx.HTTPStatusError: For non-401 HTTP errors from the adapter.
        """
        if self._oauth_grant_repo is None or self._crypto is None or self._oauth_service is None:
            raise RuntimeError("Calendar token dependencies are not configured")

        grant = await self._oauth_grant_repo.get_by_user_id(user_id)
        if grant is None:
            raise CalendarGrantMissingError()

        access_token = self._crypto.decrypt(grant.access_token_enc)

        try:
            return await fn(access_token)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 401:
                raise
            tokens = await self._oauth_service.refresh_google_token(user_id)
            if tokens is None:
                raise CalendarGrantMissingError() from exc
            return await fn(tokens.access_token)

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

    async def _create_calendar_event(
        self,
        user_id: UUID,
        candidate_id: UUID,
        spec: CalendarEventSpec,
    ) -> CalendarEvent:
        if self._calendar_port is None:
            raise RuntimeError("Calendar port is not configured")
        try:
            return await self._with_calendar_token(
                user_id,
                lambda token: self._calendar_port.create_event(token, spec),
            )
        except Exception as exc:
            await self._session.rollback()
            await log_audit(
                session=self._session,
                operation_type="interview_schedule_failed",
                entity_type="candidate",
                entity_id=candidate_id,
                user_id=user_id,
                new_value={
                    "attempted_action": "schedule_interview",
                    "candidate_id": str(candidate_id),
                    "error": str(exc),
                },
                change_summary="Interview schedule failed: Calendar event creation error",
                success=False,
            )
            await self._session.commit()
            raise CalendarEventCreateFailedError() from exc

    async def _persist_interview_schedule(
        self,
        candidate: Candidate,
        event_id: str,
        start_resolved: datetime,
        timezone: str,
    ) -> Candidate:
        candidate.status = CandidateStatus.INTERVIEW_SCHEDULED
        candidate.calendar_event_id = event_id
        candidate.interview_start_at = start_resolved
        candidate.interview_timezone = timezone
        candidate = await self._candidate_repo.update(candidate)
        await self._session.commit()
        return candidate

    async def _send_interview_email_notification(
        self,
        candidate: Candidate,
        spec: CalendarEventSpec,
    ) -> None:
        if not candidate.email:
            return
        subject = f"Interview Scheduled: {spec.summary}"
        body_html = f"<p>Your interview has been scheduled for {spec.start.isoformat()}.</p>"
        # We don't fail the whole process if email fails
        try:
            await self.send_email_to_candidate(candidate.id, subject, body_html)
        except Exception as e:
            logger.warning(f"Failed to send interview notification email to {candidate.id}: {e}")

    async def _audit_interview_schedule(
        self,
        user_id: UUID,
        candidate: Candidate,
        event_id: str,
        start_resolved: datetime,
        timezone: str,
        interviewer_ids: list[UUID],
        previous_status: str,
    ) -> None:
        await log_audit(
            session=self._session,
            operation_type="interview_scheduled",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=user_id,
            previous_value={"status": previous_status},
            new_value={
                "status": CandidateStatus.INTERVIEW_SCHEDULED,
                "calendar_event_id": event_id,
                "candidate_id": str(candidate.id),
                "start": start_resolved.isoformat(),
                "timezone": timezone,
                "interviewer_ids": [str(id_) for id_ in interviewer_ids],
            },
            change_summary=(
                f"Interview scheduled with {len(interviewer_ids)} interviewer(s); event {event_id}"
            ),
            success=True,
        )
        await self._session.commit()

    async def _create_calendar_event(
        self,
        user_id: UUID,
        candidate_id: UUID,
        calendar_port: Any,
        spec: CalendarEventSpec,
    ) -> CalendarEvent:
        try:
            return await self._with_calendar_token(
                user_id,
                lambda token: calendar_port.create_event(token, spec),
            )
        except Exception as exc:
            await self._session.rollback()
            await log_audit(
                session=self._session,
                operation_type="interview_schedule_failed",
                entity_type="candidate",
                entity_id=candidate_id,
                user_id=user_id,
                new_value={
                    "attempted_action": "schedule_interview",
                    "candidate_id": str(candidate_id),
                    "error": str(exc),
                },
                change_summary="Interview schedule failed: Calendar event creation error",
                success=False,
            )
            await self._session.commit()
            raise CalendarEventCreateFailedError() from exc

    async def _persist_interview_schedule(
        self,
        candidate: Candidate,
        event_id: str,
        start_resolved: datetime,
        timezone: str,
    ) -> Candidate:
        candidate.status = CandidateStatus.INTERVIEW_SCHEDULED
        candidate.calendar_event_id = event_id
        candidate.interview_start_at = start_resolved
        candidate.interview_timezone = timezone
        candidate = await self._candidate_repo.update(candidate)
        await self._session.commit()
        return candidate

    async def _audit_interview_schedule(
        self,
        user_id: UUID,
        candidate: Candidate,
        event_id: str,
        start_resolved: datetime,
        timezone: str,
        interviewer_ids: list[UUID],
        previous_status: str,
    ) -> None:
        await log_audit(
            session=self._session,
            operation_type="interview_scheduled",
            entity_type="candidate",
            entity_id=candidate.id,
            user_id=user_id,
            previous_value={"status": previous_status},
            new_value={
                "status": CandidateStatus.INTERVIEW_SCHEDULED,
                "calendar_event_id": event_id,
                "candidate_id": str(candidate.id),
                "start": start_resolved.isoformat(),
                "timezone": timezone,
                "interviewer_ids": [str(id_) for id_ in interviewer_ids],
            },
            change_summary=(
                f"Interview scheduled with {len(interviewer_ids)} interviewer(s); event {event_id}"
            ),
            success=True,
        )
        await self._session.commit()
