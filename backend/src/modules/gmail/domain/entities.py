"""Domain entities for the Gmail Integration module.

Defines the SQLModel table classes for EmailMessage, SyncCursor,
GmailLabelMapping, EmailAttachment, GmailAuditLog, and OutboundEmail
that map to PostgreSQL tables used for Gmail email management,
synchronization, and outbound sending.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class EmailMessage(SQLModel, table=True):
    """Represents an email fetched from Gmail and stored locally.

    Stores email metadata (subject, sender, recipients, labels) for
    search and display without requiring Gmail API calls. The raw_payload
    is encrypted with AES-256-GCM for security.
    """

    __tablename__ = "email_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    gmail_message_id: str = Field(max_length=255, unique=True, nullable=False, index=True)
    gmail_thread_id: str = Field(max_length=255, nullable=False, index=True)
    subject: str = Field(default="", max_length=998, nullable=False)
    sender_email: str = Field(default="", max_length=255, nullable=False)
    sender_name: str = Field(default="", max_length=255, nullable=False)
    recipient_emails: list[str] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )
    cc_emails: list[str] = Field(default_factory=list, sa_column=Column(JSONB, nullable=False))
    received_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    snippet: str = Field(default="", max_length=200, nullable=False)
    label_ids: list[str] = Field(default_factory=list, sa_column=Column(JSONB, nullable=False))
    has_attachments: bool = Field(default=False, nullable=False)
    raw_payload_enc: str | None = Field(default=None)
    processing_status: str = Field(default="unprocessed", max_length=20, nullable=False)
    category: str | None = Field(default=None, max_length=20)
    retry_count: int = Field(default=0, nullable=False)
    is_permanently_failed: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SyncCursor(SQLModel, table=True):
    """Tracks the Gmail history_id for incremental email synchronization.

    One cursor per user. The history_id is used with Gmail's history.list
    API to fetch only emails newer than the last successful poll.
    """

    __tablename__ = "sync_cursors"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", unique=True, nullable=False)
    history_id: str = Field(max_length=50, nullable=False)
    last_poll_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class GmailLabelMapping(SQLModel, table=True):
    """Maps VroomHR label names to Gmail internal label IDs.

    Stores the relationship between human-readable label names
    (e.g., "VroomHR/processed") and Gmail's opaque label IDs per user.
    """

    __tablename__ = "gmail_label_mappings"
    __table_args__ = (UniqueConstraint("user_id", "label_name"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    label_name: str = Field(max_length=100, nullable=False)
    gmail_label_id: str = Field(max_length=255, nullable=False)
    is_initialized: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class EmailAttachment(SQLModel, table=True):
    """Represents an attachment belonging to a fetched email.

    Stores attachment metadata and optional storage path for
    downloaded attachment binary data used by downstream pipelines.
    """

    __tablename__ = "email_attachments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email_message_id: UUID = Field(foreign_key="email_messages.id", nullable=False, index=True)
    gmail_attachment_id: str = Field(max_length=255, nullable=False)
    filename: str = Field(max_length=255, nullable=False)
    mime_type: str = Field(max_length=100, nullable=False)
    size_bytes: int = Field(nullable=False)
    storage_path: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class GmailAuditLog(SQLModel, table=True):
    """Audit trail entry for Gmail API operations.

    Records all Gmail operations (fetch, send, label_modify, connect,
    disconnect) for debugging and compliance. Does NOT store email body
    content, snippets, or attachment binary data.
    """

    __tablename__ = "gmail_audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    operation_type: str = Field(max_length=50, nullable=False)
    message_count: int = Field(default=0, nullable=False)
    success: bool = Field(nullable=False)
    metadata_: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSONB, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class OutboundEmail(SQLModel, table=True):
    """Tracks an outbound email command created by HR confirmation.

    Each row represents one send command. The lifecycle is:
    pending -> sending -> sent | failed.

    The idempotency_key prevents duplicate sends on retry.
    The email is sent using the Organization Google Connection
    token, not the creating HR user's personal token.
    """

    __tablename__ = "outbound_emails"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    idempotency_key: str = Field(
        max_length=64, unique=True, nullable=False, index=True
    )
    candidate_id: UUID | None = Field(
        default=None, foreign_key="recruitment_candidates.id", nullable=True
    )
    subject: str = Field(max_length=998, nullable=False)
    body_html: str = Field(nullable=False)
    recipient_email: str = Field(max_length=255, nullable=False)
    sender_email: str | None = Field(default=None, max_length=255)
    status: str = Field(default="pending", max_length=20, nullable=False, index=True)
    gmail_message_id: str | None = Field(default=None, max_length=255)
    gmail_thread_id: str | None = Field(default=None, max_length=255)
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0, nullable=False)
    max_retries: int = Field(default=3, nullable=False)
    last_retry_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_by_user_id: UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
