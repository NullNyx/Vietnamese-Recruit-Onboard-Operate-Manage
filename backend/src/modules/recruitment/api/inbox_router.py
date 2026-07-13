"""FastAPI router for the Recruitment Inbox.

Defines the /api/recruitment/inbox/* endpoints for listing, viewing,
correcting intent, and dismissing inbox items. All endpoints require
HR-level authentication.

Recruitment Inbox is the unified HR surface for email and Job Application
work; it is not a Gmail inbox or an AI error queue.
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.container import get_current_user, get_db_session
from src.modules.identity.domain.entities import User, UserRole
from src.modules.recruitment.api.schemas import (
    CorrectIntentRequest,
    InboxItemResponse,
    InboxListResponse,
)
from src.modules.recruitment.application.inbox_service import (
    InboxItemDismissedError,
    InboxService,
    RecruitmentInboxItemNotFoundError,
)
from src.modules.recruitment.domain.enums import InboxStatus
from src.modules.recruitment.infrastructure.repositories import (
    RecruitmentInboxItemRepository,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/recruitment/inbox", tags=["recruitment-inbox"])

# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


def _require_hr(current_user: User) -> None:
    """Guard: require HR role for inbox operations."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Chỉ HR mới có quyền truy cập Recruitment Inbox",
        )


def _build_inbox_service(
    session: AsyncSession,
    inbox_repo: RecruitmentInboxItemRepository,
) -> InboxService:
    """Build an InboxService for a database session and repository."""
    return InboxService(
        session=session,
        inbox_repo=inbox_repo,
    )


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

CurrentUserDep = Annotated[User, Depends(get_current_user)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_inbox_repo(
    session: AsyncSession = Depends(get_db_session),
) -> RecruitmentInboxItemRepository:
    """Provide a RecruitmentInboxItemRepository via DI."""
    return RecruitmentInboxItemRepository(session)


# ---------------------------------------------------------------------------
# Valid filter values for documentation
# ---------------------------------------------------------------------------

_VALID_FILTERS = [
    InboxStatus.NEEDS_CLASSIFICATION,
    InboxStatus.NEEDS_INFORMATION,
    InboxStatus.READY_FOR_REVIEW,
    InboxStatus.RESOLVED,
]
_VALID_FILTER_STR = ", ".join(v.value for v in _VALID_FILTERS)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=InboxListResponse)
async def list_inbox(
    current_user: CurrentUserDep,
    session: DbSessionDep,
    inbox_repo: RecruitmentInboxItemRepository = Depends(get_inbox_repo),
    inbox_status: str | None = Query(
        default=None,
        description=f"Filter by inbox status ({_VALID_FILTER_STR})",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
) -> InboxListResponse:
    """List Recruitment Inbox items with optional status filter.

    Filters:
    - needs_classification: Emails below policy threshold or exhausted retry.
    - needs_information: Emails needing additional information.
    - ready_for_review: Job Applications ready for HR review.
    - resolved: Items that have been handled.

    By default, returns all non-dismissed items. Dismissed items are
    excluded from the default list but retained for audit.
    """
    _require_hr(current_user)

    # Validate filter value if provided
    if inbox_status is not None:
        valid_values = {v.value for v in _VALID_FILTERS}
        if inbox_status not in valid_values:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid inbox_status '{inbox_status}'. Valid values: {_VALID_FILTER_STR}"
                ),
            )

    service = _build_inbox_service(session, inbox_repo)
    items, total = await service.list_inbox(
        inbox_status=inbox_status,
        page=page,
        page_size=page_size,
    )

    return InboxListResponse(
        items=[InboxItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{item_id}", response_model=InboxItemResponse)
async def get_inbox_item(
    item_id: UUID,
    current_user: CurrentUserDep,
    session: DbSessionDep,
    inbox_repo: RecruitmentInboxItemRepository = Depends(get_inbox_repo),
) -> InboxItemResponse:
    """Get a single Recruitment Inbox item with full detail.

    Shows prediction, calibrated confidence, evidence, source hints,
    attachment metadata, correction history, and dismissal audit.
    """
    _require_hr(current_user)

    service = _build_inbox_service(session, inbox_repo)
    try:
        item = await service.get_item(item_id)
    except RecruitmentInboxItemNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Recruitment Inbox item not found",
        )

    return InboxItemResponse.model_validate(item)


@router.post("/{item_id}/correct-intent", response_model=InboxItemResponse)
async def correct_inbox_intent(
    item_id: UUID,
    body: CorrectIntentRequest,
    current_user: CurrentUserDep,
    session: DbSessionDep,
    inbox_repo: RecruitmentInboxItemRepository = Depends(get_inbox_repo),
) -> InboxItemResponse:
    """Correct the routing intent of an inbox item.

    Records the correction in audit history and resolves the item.
    Dismissed items cannot be corrected.
    """
    _require_hr(current_user)

    service = _build_inbox_service(session, inbox_repo)
    try:
        item = await service.correct_intent(
            item_id=item_id,
            corrected_intent=body.corrected_intent,
            user_id=current_user.id,
        )
    except RecruitmentInboxItemNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Recruitment Inbox item not found",
        )
    except InboxItemDismissedError:
        raise HTTPException(
            status_code=409,
            detail="Cannot modify a dismissed inbox item",
        )

    return InboxItemResponse.model_validate(item)


@router.post("/{item_id}/dismiss", response_model=InboxItemResponse)
async def dismiss_inbox_item(
    item_id: UUID,
    current_user: CurrentUserDep,
    session: DbSessionDep,
    inbox_repo: RecruitmentInboxItemRepository = Depends(get_inbox_repo),
) -> InboxItemResponse:
    """Dismiss an inbox item.

    Dismissed items retain their audit record and are protected from
    worker retry recreation. The action is idempotent — dismissing an
    already dismissed item returns the current state without error.
    """
    _require_hr(current_user)

    service = _build_inbox_service(session, inbox_repo)
    try:
        item = await service.dismiss_item(
            item_id=item_id,
            user_id=current_user.id,
        )
    except RecruitmentInboxItemNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Recruitment Inbox item not found",
        )
    except InboxItemDismissedError:
        # Idempotent: already dismissed is not an error
        item = await service.get_item(item_id)

    return InboxItemResponse.model_validate(item)
