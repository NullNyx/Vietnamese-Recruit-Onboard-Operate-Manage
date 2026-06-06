"""FastAPI router for the AI Assistant module.

Defines POST /api/assistant/chat — the single endpoint for the
conversational AI Assistant.

Requires any authenticated user. Conversation history is
held in frontend memory; backend processes each turn statelessly.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.assistant.api.schemas import (
    ChatMessageSchema,
    ChatRequest,
    ChatResponseSchema,
    DraftActionSchema,
)
from src.modules.assistant.application.assistant_service import (
    AssistantService,
    ChatMessage,
)
from src.modules.assistant.container import get_assistant_service
from src.modules.assistant.infrastructure.tool_config_repository import (
    ToolConfigRepository,
)
from src.modules.identity.api.router import get_current_user
from src.modules.identity.container import get_db_session
from src.modules.identity.domain.entities import User

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

CurrentUserDep = Annotated[User, Depends(get_current_user)]
AssistantServiceDep = Annotated[AssistantService, Depends(get_assistant_service)]


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
    _user: CurrentUserDep,
    assistant_service: AssistantServiceDep,
    session: AsyncSession = Depends(get_db_session),
) -> ChatResponseSchema:
    """Chat with the AI Assistant.

    Receives the full conversation history (frontend holds state).
    The last message must be from the user. Returns new assistant
    messages and optionally a Draft Action for HR to review.

    Requires any authenticated user.
    """
    # Validate last message is from user
    last_msg = body.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(status_code=422, detail="Last message must be from user")

    # Fetch enabled tool names from DB config
    tool_config_repo = ToolConfigRepository(session)
    enabled_tool_names = await tool_config_repo.get_enabled_tool_names()

    # Convert schema to domain messages
    domain_messages = [
        ChatMessage(
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls,
            tool_call_id=m.tool_call_id,
            name=m.name,
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
        ChatMessageSchema(
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

    return ChatResponseSchema(
        messages=new_messages,
        draft_action=draft_action,
    )
