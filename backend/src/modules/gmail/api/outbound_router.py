"""FastAPI router for outbound email lifecycle endpoints.

Defines the /api/outbound-emails/* endpoints for creating, listing,
viewing status, and retrying outbound emails. All endpoints require
authentication.
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gmail.api.schemas import (
    OutboundEmailCreateRequest,
    OutboundEmailListResponse,
    OutboundEmailResponse,
    OutboundEmailRetryResponse,
)
from src.modules.gmail.domain.exceptions import (
    GmailSendFailedException,
    OrganizationNotConnectedError,
    OutboundEmailAlreadySentError,
    OutboundEmailMaxRetriesExceededError,
    OutboundEmailNotFoundError,
)
from src.modules.gmail.infrastructure.outbound_email_repository import (
    OutboundEmailRepository,
)
from src.modules.identity.container import get_current_user, get_db_session
from src.modules.identity.domain.entities import User, UserRole
from src.modules.recruitment.infrastructure.repositories import CandidateRepository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/outbound-emails", tags=["outbound-emails"])

CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def require_admin(current_user: CurrentUserDep) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


AdminUserDep = Annotated[User, Depends(require_admin)]


async def get_outbound_service_dep(
    session: AsyncSession = Depends(get_db_session),
) -> OutboundEmailService:
    """FastAPI dependency: provide an OutboundEmailService."""
    from src.modules.gmail.container import build_outbound_email_service

    return await build_outbound_email_service(session)


from src.modules.gmail.application.outbound_email_service import (  # noqa: E402
    OutboundEmailService,
)

OutboundServiceDep = Annotated[OutboundEmailService, Depends(get_outbound_service_dep)]


# ---------------------------------------------------------------------------
# Create outbound email
# ---------------------------------------------------------------------------


@router.post("", response_model=OutboundEmailResponse, status_code=201)
async def create_outbound_email(
    body: OutboundEmailCreateRequest,
    current_user: AdminUserDep,
    outbound_service: OutboundServiceDep,
    session: AsyncSession = Depends(get_db_session),
) -> OutboundEmailResponse:
    """Create an outbound email command (pending status).

    Does NOT send the email — only creates the command record.
    """
    # Validate candidate exists if candidate_id provided
    if body.candidate_id is not None:
        candidate_repo = CandidateRepository(session)
        candidate = await candidate_repo.get_by_id(body.candidate_id)
        if candidate is None:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate not found: {body.candidate_id}",
            )

    outbound = await outbound_service.create_outbound(
        candidate_id=body.candidate_id,
        recipient_email=body.recipient_email,
        subject=body.subject,
        body_html=body.body_html,
        created_by_user_id=current_user.id,
        hr_user=current_user,
    )

    return OutboundEmailResponse.model_validate(outbound)


# ---------------------------------------------------------------------------
# Get outbound email status
# ---------------------------------------------------------------------------


@router.get("/{outbound_id}", response_model=OutboundEmailResponse)
async def get_outbound_email(
    outbound_id: UUID,
    current_user: CurrentUserDep,
    outbound_service: OutboundServiceDep,
) -> OutboundEmailResponse:
    """Get the current status of an outbound email."""
    try:
        outbound = await outbound_service.get_outbound(outbound_id)
    except OutboundEmailNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return OutboundEmailResponse.model_validate(outbound)


# ---------------------------------------------------------------------------
# List outbound emails for a candidate
# ---------------------------------------------------------------------------


@router.get("", response_model=OutboundEmailListResponse)
async def list_outbound_emails(
    current_user: CurrentUserDep,
    outbound_service: OutboundServiceDep,
    session: AsyncSession = Depends(get_db_session),
    candidate_id: UUID | None = Query(default=None, description="Filter by candidate UUID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> OutboundEmailListResponse:
    """List outbound emails, optionally filtered by candidate."""
    if candidate_id is not None:
        items, total = await outbound_service.list_for_candidate(
            candidate_id=candidate_id,
            page=page,
            page_size=page_size,
        )
    else:
        repo = OutboundEmailRepository(session)
        items = await repo.list_by_status("", limit=page_size)
        total = len(items)

    return OutboundEmailListResponse(
        items=[OutboundEmailResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Send / process a pending outbound email
# ---------------------------------------------------------------------------


@router.post("/{outbound_id}/send", response_model=OutboundEmailResponse)
async def send_outbound_email(
    outbound_id: UUID,
    current_user: AdminUserDep,
    outbound_service: OutboundServiceDep,
) -> OutboundEmailResponse:
    """Send a pending outbound email immediately.

    Uses the Organization Google Connection token.
    """
    try:
        outbound = await outbound_service.send_outbound(
            outbound_id,
            hr_user=current_user,
        )
    except OutboundEmailNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OutboundEmailAlreadySentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OrganizationNotConnectedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GmailSendFailedException as exc:
        try:
            outbound = await outbound_service.get_outbound(outbound_id)
            return OutboundEmailResponse.model_validate(outbound)
        except OutboundEmailNotFoundError:
            raise HTTPException(status_code=502, detail=f"Send failed: {exc}") from exc

    return OutboundEmailResponse.model_validate(outbound)


# ---------------------------------------------------------------------------
# Retry a failed outbound email
# ---------------------------------------------------------------------------


@router.post("/{outbound_id}/retry", response_model=OutboundEmailRetryResponse)
async def retry_outbound_email(
    outbound_id: UUID,
    current_user: AdminUserDep,
    outbound_service: OutboundServiceDep,
) -> OutboundEmailRetryResponse:
    """Retry a failed outbound email.

    Validates retry constraints, then re-sends.
    """
    try:
        outbound = await outbound_service.retry_outbound(
            outbound_id,
            hr_user=current_user,
        )
    except OutboundEmailNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OutboundEmailAlreadySentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OutboundEmailMaxRetriesExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OrganizationNotConnectedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GmailSendFailedException as exc:
        try:
            outbound = await outbound_service.get_outbound(outbound_id)
            return OutboundEmailRetryResponse(
                id=outbound.id,
                status=outbound.status,
                message=f"Retry failed: {exc}",
            )
        except OutboundEmailNotFoundError:
            raise HTTPException(status_code=502, detail=f"Retry failed: {exc}") from exc

    return OutboundEmailRetryResponse(
        id=outbound.id,
        status=outbound.status,
        message="Retry initiated",
    )
