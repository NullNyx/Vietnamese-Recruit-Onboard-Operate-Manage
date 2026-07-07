"""Gmail module configuration.

Loads Gmail module settings from environment variables with the GMAIL_ prefix.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GmailSettings(BaseSettings):
    """Gmail module configuration loaded from environment variables.

    All environment variables are prefixed with ``GMAIL_``. For example,
    ``poll_interval_seconds`` maps to ``GMAIL_POLL_INTERVAL_SECONDS``.

    Attributes:
        poll_interval_seconds: Interval between email poll cycles in seconds.
        batch_size: Maximum number of emails to fetch per poll cycle.
        initial_sync_days: Number of days to look back on first sync.
        manual_sync_cooldown_seconds: Minimum seconds between manual syncs.
        quota_units_per_second: Gmail API quota units allowed per user per second.
        max_retries: Maximum retry attempts for failed Gmail API calls.
        retry_backoff_base: Base delay in seconds for exponential backoff.
        max_retry_after_seconds: Maximum Retry-After duration to honor.
        permanent_failure_threshold: Consecutive failures before marking permanent.
        api_timeout_seconds: Timeout for general Gmail API requests.
        revocation_timeout_seconds: Timeout for token revocation calls.
        body_fetch_timeout_seconds: Timeout for fetching full email body.
        max_attachment_size_bytes: Maximum allowed attachment size in bytes.
        max_attachments_per_email: Maximum attachments to process per email.
        allowed_mime_types: List of MIME types accepted for attachments.
        label_prefix: Namespace prefix for HRSpace Gmail labels.
        required_labels: Label names (without prefix) to create on connection.
        classification_batch_concurrency: Max simultaneous AI classification calls.
        classification_request_timeout_seconds: Overall endpoint time budget in seconds.
        audit_retention_days: Days to retain audit log entries.
        audit_subject_max_length: Maximum subject length in audit logs.
    """

    model_config = SettingsConfigDict(env_prefix="GMAIL_")

    # Polling
    poll_interval_seconds: int = Field(default=300, ge=60, le=3600)
    batch_size: int = Field(default=100, ge=1, le=100)
    initial_sync_days: int = Field(default=7, ge=1, le=30)

    # Rate limiting
    manual_sync_cooldown_seconds: int = Field(default=30, ge=10)
    quota_units_per_second: int = Field(default=250)

    # Retry
    max_retries: int = Field(default=3)
    retry_backoff_base: float = Field(default=1.0)
    max_retry_after_seconds: int = Field(default=120)
    permanent_failure_threshold: int = Field(default=5)

    # Timeouts
    api_timeout_seconds: int = Field(default=30)
    revocation_timeout_seconds: int = Field(default=10)
    body_fetch_timeout_seconds: int = Field(default=10)

    # Attachments
    max_attachment_size_bytes: int = Field(default=10 * 1024 * 1024)
    max_attachments_per_email: int = Field(default=20)
    allowed_mime_types: list[str] = Field(
        default=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/jpeg",
            "image/png",
        ]
    )

    # Labels
    label_prefix: str = Field(default="HRSpace/")
    required_labels: list[str] = Field(
        default=[
            "processed",
            # Recruitment pipeline
            "recruitment",
            "interview",
            "offer",
            "onboarding",
            # Employee relations
            "leave_request",
            "payroll",
            "employee_request",
            "resignation",
            "complaint",
            # External
            "vendor",
            "insurance",
            # Internal & compliance
            "internal",
            "compliance",
            # System
            "notification",
            "uncategorized",
        ]
    )

    # Classification (AI)
    classification_llm_base_url: str = Field(default="https://token-plan-sgp.xiaomimimo.com/v1")
    classification_llm_api_key: str = Field(default="")
    classification_llm_model: str = Field(default="mimo-v2.5")
    classification_llm_timeout_seconds: int = Field(default=15, gt=0)
    classification_llm_max_retries: int = Field(default=3, ge=1)
    classification_confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    classification_needs_review_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    classification_enabled: bool = Field(default=True)
    # Max simultaneous AI classification calls in a batch
    classification_batch_concurrency: int = Field(default=3, ge=1, le=10)
    # Overall endpoint time budget for the classify request
    classification_request_timeout_seconds: int = Field(default=60, gt=0)

    # Audit
    audit_retention_days: int = Field(default=90)
    audit_subject_max_length: int = Field(default=100)
