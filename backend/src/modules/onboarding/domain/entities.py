"""Domain entities for the Onboarding module.

Defines the SQLModel table classes for OnboardingProcess, OnboardingTask, and
OnboardingAuditLog that map to PostgreSQL tables used to drive an accepted
Candidate through a checklist-driven process to an active Employee.

The ``Employee`` entity is reused unchanged from the employee module; this
module only owns the process, task, and audit tables. The unique constraint on
``OnboardingProcess.candidate_id`` is the backbone of idempotent event
consumption (exactly one process per candidate), and the append-only
``OnboardingAuditLog`` records both system-driven (event consumption) and
HR-driven (task completion, activation) state changes.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class OnboardingProcess(SQLModel, table=True):
    """Tracks one Employee's onboarding from acceptance to activation.

    Created exactly once per accepted Candidate when a ``candidate_accepted``
    event is consumed. The ``candidate_id`` column is unique and indexed so
    that "exactly one process per candidate" is a database invariant rather
    than only application logic, enabling safe idempotent event re-delivery.
    The linked Employee starts inactive and is activated when every task in the
    checklist reaches ``done``.
    """

    __tablename__ = "onboarding_processes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    candidate_id: UUID = Field(unique=True, nullable=False, index=True)
    employee_id: UUID = Field(foreign_key="employees.id", nullable=False, index=True)
    status: str = Field(default="in_progress", max_length=20, nullable=False, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
    )


class OnboardingTask(SQLModel, table=True):
    """A single item in an OnboardingProcess checklist.

    Each process is created with a fixed four-item checklist in a stable order
    (tracked by ``order_index``). A task has a ``task_key`` (stable enum key)
    and a human-readable ``name`` (display name), and its status is restricted
    by the application to ``pending`` or ``done``. Completion metadata records
    when and by which HR user the task was marked done.
    """

    __tablename__ = "onboarding_tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    process_id: UUID = Field(foreign_key="onboarding_processes.id", nullable=False, index=True)
    task_key: str = Field(max_length=40, nullable=False)
    name: str = Field(max_length=100, nullable=False)
    status: str = Field(default="pending", max_length=10, nullable=False)
    order_index: int = Field(nullable=False)
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
    )
    completed_by_user_id: UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class OnboardingAuditLog(SQLModel, table=True):
    """Append-only audit entry for onboarding operations.

    Records both system-driven events (event consumption, duplicate detection,
    rejection, failure) and HR-driven actions (task completion, activation).
    ``user_id`` is nullable because system/consumer events have no acting HR
    user. The audit write participates in the same transaction as the state
    change it records, so a failed audit append rolls back the state change.
    UPDATE/DELETE on this table are not permitted by the application.
    """

    __tablename__ = "onboarding_audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    actor_email: str | None = Field(default=None, max_length=255)
    operation_type: str = Field(max_length=50, nullable=False, index=True)
    entity_type: str = Field(max_length=50, nullable=False)
    entity_id: UUID | None = Field(default=None, index=True)
    candidate_id: UUID | None = Field(default=None, index=True)
    event_id: str | None = Field(default=None, max_length=255)
    previous_value: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    new_value: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    change_summary: str | None = Field(default=None, max_length=500)
    success: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class OnboardingDocument(SQLModel, table=True):
    """A document item in an onboarding process checklist.

    Each onboarding process has a predefined set of document items (CCCD,
    degree, etc.) generated from DOCUMENT_TEMPLATE at process creation.
    Documents are uploaded by HR, then verified or rejected.
    """

    __tablename__ = "onboarding_documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    process_id: UUID = Field(foreign_key="onboarding_processes.id", nullable=False, index=True)
    document_type: str = Field(max_length=40, nullable=False)
    display_name: str = Field(max_length=100, nullable=False)
    is_required: bool = Field(default=True, nullable=False)
    status: str = Field(default="pending", max_length=20, nullable=False)
    file_name: str | None = Field(default=None, max_length=255)
    file_size: int | None = Field(default=None)
    mime_type: str | None = Field(default=None, max_length=100)
    storage_path: str | None = Field(default=None)
    reject_reason: str | None = Field(default=None, max_length=500)
    uploaded_by_hr_id: UUID | None = Field(default=None, foreign_key="users.id")
    uploaded_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    verified_by_hr_id: UUID | None = Field(default=None, foreign_key="users.id")
    verified_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ai_extraction: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

class OnboardingContractDraft(SQLModel, table=True):
    """Contract draft scoped to an onboarding process.

    Holds the draft content HR edits during onboarding. When the onboarding
    process completes and the employee is activated, this draft serves as the
    basis for creating a formal Contract in the employee module.

    Status: draft / ready / sent / signed.
    Exactly one draft per onboarding process (unique process_id).
    """

    __tablename__ = "onboarding_contract_drafts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    process_id: UUID = Field(
        foreign_key="onboarding_processes.id",
        nullable=False,
        index=True,
        unique=True,
    )
    contract_type: str = Field(max_length=30, nullable=False)
    content: str | None = Field(default=None)
    status: str = Field(default="draft", max_length=20, nullable=False)
    revision: int = Field(default=1, nullable=False)
    created_by: UUID | None = Field(default=None, foreign_key="users.id")
    updated_by: UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
