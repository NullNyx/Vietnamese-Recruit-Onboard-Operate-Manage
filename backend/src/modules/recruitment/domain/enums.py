"""Domain enums for the Recruitment CV Pipeline module.

Defines the enumeration types used across the recruitment module
for candidate lifecycle status, CV processing status, and email
intent classification.
"""

from enum import StrEnum


class CandidateStatus(StrEnum):
    """Lifecycle status of a candidate in the recruitment pipeline.

    Transitions follow a defined state machine:
    - new → reviewing, interview_scheduled, rejected, archived
    - reviewing → interview_scheduled, accepted, rejected, archived
    - interview_scheduled → accepted, rejected, archived
    - accepted → (no transitions)
    - rejected → (no transitions)
    - archived → (idempotent re-archive only)
    """

    NEW = "new"
    REVIEWING = "reviewing"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ProcessingStatus(StrEnum):
    """Status of CV document processing through the pipeline.

    Tracks the progress of a CV document from initial upload
    through OCR extraction, LLM parsing, and final validation.
    """

    PENDING = "pending"
    OCR_PROCESSING = "ocr_processing"
    LLM_PARSING = "llm_parsing"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"
    SKIPPED = "skipped"
    DISMISSED = "dismissed"
    UPLOAD_FAILED = "upload_failed"
    PERMANENTLY_FAILED = "permanently_failed"
    AI_UNAVAILABLE = "ai_unavailable"


class EmailIntent(StrEnum):
    """Classification intent for incoming emails.

    Determined by the AI Intent Classifier using LLM analysis
    of email subject, sender, snippet, and attachment metadata.
    """

    CV = "cv"
    JOB_APPLICATION = "job_application"
    PARTNER = "partner"
    EVENT = "event"
    INTERNAL = "internal"
    OTHER = "other"


class JobOpeningStatus(StrEnum):
    """Lifecycle status of a Job Opening in recruitment planning.

    Transitions follow a defined state machine:
    - draft → open, cancelled
    - open → closed, cancelled
    - closed → open (reopen)
    - cancelled → (terminal, no transitions)
    """

    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ApplicationSource(StrEnum):
    """Source channel of a Job Application.

    Identifies how the application was received:
    - direct: Applicant sent directly to the organization.
    - employee_referral: Referred by an existing employee.
    - agency: Submitted through a recruitment agency.
    """

    DIRECT = "direct"
    EMPLOYEE_REFERRAL = "employee_referral"
    AGENCY = "agency"


class JobApplicationStatus(StrEnum):
    """Lifecycle status of a Job Application.

    - new: Freshly ingested, awaiting HR review.
    - dismissed: Rejected by HR; kept for idempotency.
    - promoted: Converted to Candidate by HR action.
    """

    NEW = "new"
    DISMISSED = "dismissed"
    PROMOTED = "promoted"


class JobApplicationProcessingStatus(StrEnum):
    """Processing status of a Job Application in the ingestion pipeline.

    - pending: Awaiting processing.
    - completed: Successfully ingested.
    - failed: Ingestion failed (provider error).
    - permanently_failed: All retries exhausted.
    """

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    PERMANENTLY_FAILED = "permanently_failed"
