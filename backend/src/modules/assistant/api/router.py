"""FastAPI router for the AI Assistant module.

Defines POST /api/assistant/chat — the single endpoint for the
conversational AI Assistant.

Requires admin role. Conversation history is
held in frontend memory; backend processes each turn statelessly.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.assistant.api.schemas import (
    ChatRequest,
    ChatResponseSchema,
    DraftActionSchema,
    DraftDecisionRequest,
    OutgoingMessageSchema,
)
from src.modules.assistant.application.assistant_service import (
    AssistantService,
    ChatMessage,
)
from src.modules.assistant.container import get_assistant_service
from src.modules.assistant.infrastructure.tool_config_repository import (
    ToolConfigRepository,
)
from src.modules.identity.api.admin_router import require_admin
from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.container import get_audit_service, get_db_session
from src.modules.identity.domain.entities import AuditActionType, User

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

AdminUserDep = Annotated[User, Depends(require_admin)]
AssistantServiceDep = Annotated[AssistantService, Depends(get_assistant_service)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post(
    "/chat",
    response_model=ChatResponseSchema,
)
async def chat(
    body: ChatRequest,
    _user: AdminUserDep,
    assistant_service: AssistantServiceDep,
    audit_service: AuditServiceDep,
    session: AsyncSession = Depends(get_db_session),
) -> ChatResponseSchema:
    """Chat with the AI Assistant.

    Receives the full conversation history (frontend holds state).
    The last message must be from the user. Returns new assistant
    messages and optionally a Draft Action for HR to review.

    Requires admin role. Logs audit when a Draft Action is returned.
    """
    # Validate last message is from user
    last_msg = body.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(status_code=422, detail="Last message must be from user")

    # Fetch enabled tool names from DB config
    tool_config_repo = ToolConfigRepository(session)
    enabled_tool_names = await tool_config_repo.get_enabled_tool_names()

    # Convert schema to domain messages (only role + content — tool fields are
    # never accepted from the client, per ADR-0006)
    domain_messages = [
        ChatMessage(
            role=m.role,
            content=m.content,
        )
        for m in body.messages
    ]

    # Run the assistant with filtered tools
    response = await assistant_service.chat(
        domain_messages,
        enabled_tool_names=enabled_tool_names,
    )

    # Convert back to schema
    new_messages = [
        OutgoingMessageSchema(
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls,
            tool_call_id=m.tool_call_id,
            name=m.name,
        )
        for m in response.messages
    ]

    draft_action = None
    if response.draft_action:
        draft_action = DraftActionSchema(**response.draft_action)

        # Audit: log when a Draft Action is returned (HR used a Draft-Tool)
        await audit_service.log_action(
            admin=_user,
            action_type=AuditActionType.ASSISTANT_CHAT,
            details={
                "action": "draft_action_returned",
                "draft_type": response.draft_action.get("action_type"),
            },
        )

    return ChatResponseSchema(
        messages=new_messages,
        draft_action=draft_action,
    )


@router.post("/draft-decision", status_code=204)
async def record_draft_decision(
    body: DraftDecisionRequest,
    _user: AdminUserDep,
    audit_service: AuditServiceDep,
) -> None:
    """Record HR's confirm/reject decision without storing conversation text."""
    await audit_service.log_action(
        admin=_user,
        action_type=AuditActionType.ASSISTANT_CHAT,
        details={
            "event": "draft_action_decision",
            "decision": body.decision,
            "action_type": body.action_type,
            "scope": body.provenance.get("scope", "unknown"),
            "tool": body.provenance.get("tool", "unknown"),
            "version": "assistant-v1",
            "status": "confirmed" if body.decision == "confirm" else "rejected",
            "confirm_endpoint": body.confirm_endpoint,
            "parameters": {"candidate_id": body.provenance.get("candidate_id")},
        },
    )
