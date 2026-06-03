"""Pydantic schemas for the AI Assistant API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessageSchema(BaseModel):
    """A single message in the conversation.

    Attributes:
        role: Message role — user, assistant, or tool.
        content: Text content of the message.
        tool_calls: Optional tool calls from the assistant.
        tool_call_id: Optional ID linking a tool result to its call.
        name: Optional tool name for tool result messages.
    """

    role: str = Field(..., description="Message role: user, assistant, or tool")
    content: str | None = Field(default=None, description="Text content")
    tool_calls: list[dict] | None = Field(default=None, description="Tool calls from assistant")
    tool_call_id: str | None = Field(default=None, description="Tool call ID for results")
    name: str | None = Field(default=None, description="Tool name for results")


class ChatRequest(BaseModel):
    """Request body for the chat endpoint.

    Attributes:
        messages: Full conversation history including the new user message.
            The last message should be the new user message.
    """

    messages: list[ChatMessageSchema] = Field(
        ...,
        min_length=1,
        description="Conversation history. Last message must be from user.",
    )


class DraftActionSchema(BaseModel):
    """A structured proposal for HR to review and confirm.

    This is the human-in-the-loop mechanism (CONTEXT.md).
    HR reviews the preview; on confirm, the frontend calls the real endpoint.
    """

    action_type: str = Field(..., description="Action type (e.g. send_email)")
    parameters: dict = Field(..., description="Action parameters")
    preview: str = Field(..., description="Human-readable preview for HR")
    confirm_endpoint: str = Field(..., description="Real API endpoint to call on confirm")
    confirm_method: str = Field(..., description="HTTP method (POST, PATCH, etc.)")
    confirm_body: dict = Field(..., description="Request body for the confirm endpoint")


class ChatResponseSchema(BaseModel):
    """Response from the chat endpoint.

    Attributes:
        messages: New messages added during this turn (assistant + tool results).
        draft_action: Optional Draft Action if a draft tool was invoked.
    """

    messages: list[ChatMessageSchema] = Field(
        ..., description="New messages from this assistant turn"
    )
    draft_action: DraftActionSchema | None = Field(
        default=None,
        description="Draft Action for HR to review (if a draft tool was called)",
    )
