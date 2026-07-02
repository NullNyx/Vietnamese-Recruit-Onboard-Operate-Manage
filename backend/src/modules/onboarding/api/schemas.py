"""Pydantic v2 request/response schemas for the Onboarding API.

Defines the data transfer objects used by the onboarding router endpoints
(``GET /api/onboarding/processes``, ``GET /api/onboarding/processes/{id}``, and
``PATCH /api/onboarding/tasks/{id}``) for request validation and response
serialization.

Status fields are typed with the onboarding domain enums so invalid values are
rejected by Pydantic with a 422 before any service logic runs:

* :class:`~src.modules.onboarding.domain.enums.OnboardingTaskStatus` constrains
  a task status to ``{pending, done}`` (R3.5, R4.6).
* :class:`~src.modules.onboarding.domain.enums.OnboardingStatus` constrains a
  process status to ``{in_progress, complete}`` and is re-exported here so the
  router (task 14.3) can type the optional list ``status`` filter query param
  with it, rejecting any undefined value with a 422 (R6.5).

The router converts the service read-model dataclasses (``ProcessListItem``,
``PaginatedProcesses``, ``ProcessDetail``, ``ProcessTaskDetail``) into these
schemas; in particular the process ``id`` field is populated from the
dataclasses' ``process_id``.
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.onboarding.domain.enums import OnboardingStatus, OnboardingTaskStatus

__all__ = [
    "OnboardingProcessDetailResponse",
    "OnboardingProcessListItem",
    "OnboardingProcessListResponse",
    "OnboardingStatus",
    "OnboardingTaskResponse",
    "TaskStatusUpdate",
    "OnboardingCountsResponse",
    "EmployeeSetupUpdate",
    "OnboardingDocumentResponse",
    "DocumentUploadResponse",
    "DocumentVerifyRequest",
]


class OnboardingCountsResponse(BaseModel):
    """Aggregate process counts by status for tab badges.

    Returns the true total per status so the frontend can display accurate
    badge counts on filter tabs regardless of which page is loaded.

    Attributes:
        total: Total number of processes across all statuses.
        in_progress: Number of processes with status ``in_progress``.
        ready_for_completion: Number of processes with status ``ready_for_completion``.
        complete: Number of processes with status ``complete``.
    """

    total: int
    in_progress: int
    ready_for_completion: int
    complete: int


class TaskStatusUpdate(BaseModel):
    """Request body for ``PATCH /api/onboarding/tasks/{task_id}``.

    Pydantic validates ``status`` against
    :class:`~src.modules.onboarding.domain.enums.OnboardingTaskStatus`, so any
    value outside ``{pending, done}`` yields a 422 naming the field and value
    before the service is invoked (R3.5, R4.6).

    Attributes:
        status: The requested task status (``pending`` or ``done``).
    """

    status: OnboardingTaskStatus


class EmployeeSetupUpdate(BaseModel):
    """Request body for updating employee core setup fields from onboarding."""

    department_id: UUID | None = None
    position_id: UUID | None = None
    manager_id: UUID | None = None
    start_date: date | None = None


class OnboardingDocumentResponse(BaseModel):
    """A single document item in the onboarding document checklist."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    process_id: UUID
    document_type: str
    display_name: str
    is_required: bool
    status: str
    file_name: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    reject_reason: str | None = None
    uploaded_by_hr_id: UUID | None = None
    uploaded_at: str | None = None
    verified_by_hr_id: UUID | None = None
    verified_at: str | None = None
    ai_extraction: dict | None = None


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document file."""

    id: UUID
    status: str
    file_name: str
    file_size: int
    mime_type: str


class DocumentVerifyRequest(BaseModel):
    """Request body for verifying a document item."""

    verified: bool
    reject_reason: str | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class OnboardingTaskResponse(BaseModel):
    """A single onboarding task in a process detail response.

    Maps from the service ``ProcessTaskDetail`` dataclass (matching field
    names).

    Attributes:
        id: The OnboardingTask identifier.
        name: The task's human-readable display name.
        status: The task status (``pending`` or ``done``).
        order_index: The task's position in the fixed checklist (0-based).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: OnboardingTaskStatus
    order_index: int
    completed_at: str | None = None
    completed_by_name: str | None = None


class OnboardingProcessListItem(BaseModel):
    """A single onboarding process entry in the paginated list response (R6.1).

    The ``id`` field is populated from the service ``ProcessListItem``
    dataclass' ``process_id`` by the router.

    Attributes:
        id: The OnboardingProcess identifier.
        status: The process status (``in_progress`` or ``complete``).
        employee_id: The linked Employee record identifier.
        completed_count: Number of tasks with status ``done``.
        total_count: Total number of tasks in the checklist.
    """

    id: UUID
    status: OnboardingStatus
    employee_id: UUID
    employee_full_name: str
    employee_email: str
    employee_code: str | None
    completed_count: int
    total_count: int
    missing_setup_fields: list[str] = Field(default_factory=list)


class OnboardingProcessListResponse(BaseModel):
    """Paginated response for the onboarding process list endpoint (R6.2).

    ``items`` holds at most 50 processes for the requested page, while ``total``
    is the true count of processes matching the request regardless of
    pagination (zero with an empty ``items`` list when none match).

    Attributes:
        items: The list items for the requested page (length ``<= 50``).
        total: The true count of matching processes (ignoring pagination).
        page: The 1-indexed page number that was requested.
        page_size: The effective page size applied (capped at 50).
    """

    items: list[OnboardingProcessListItem]
    total: int
    page: int
    page_size: int


class OnboardingProcessDetailResponse(BaseModel):
    """Full detail of one onboarding process including its checklist (R6.3).

    Exposes the same summary fields as :class:`OnboardingProcessListItem` plus
    the ordered list of tasks (each with name and status). The ``id`` field is
    populated from the service ``ProcessDetail`` dataclass' ``process_id`` by
    the router.

    Attributes:
        id: The OnboardingProcess identifier.
        status: The process status (``in_progress`` or ``complete``).
        employee_id: The linked Employee record identifier.
        completed_count: Number of tasks with status ``done``.
        total_count: Total number of tasks in the checklist.
        tasks: The process's tasks ordered by ``order_index`` ascending.
    """

    id: UUID
    status: OnboardingStatus
    employee_id: UUID
    employee_full_name: str
    employee_email: str
    employee_code: str | None
    completed_count: int
    total_count: int
    missing_setup_fields: list[str] = Field(default_factory=list)
    completed_at: str | None = None
    accepted_at: str | None = None
    job_opening: str | None = None
    department_id: UUID | None = None
    position_id: UUID | None = None
    manager_id: UUID | None = None
    start_date: str | None = None
    tasks: list[OnboardingTaskResponse] = Field(default_factory=list)
    documents: list[OnboardingDocumentResponse] = Field(default_factory=list)
