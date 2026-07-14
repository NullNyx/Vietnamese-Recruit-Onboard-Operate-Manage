"""Pydantic schemas for the AI Assistant API.

Input/output schemas are separate (diagnosis #2):
- IncomingMessageSchema: client → server (user/assistant roles only, no tool fields)
- OutgoingMessageSchema: server → client (includes tool fields for display)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class IncomingMessageSchema(BaseModel):
    """Incoming message from the client.

    Only user and assistant roles are accepted. Tool messages are created
    server-side and must never come from the client (ADR-0006).
    """

    role: Literal["user", "assistant"] = Field(
        ...,
        description="Message role: user or assistant",
    )
    content: str | None = Field(default=None, description="Text content of the message")

    @model_validator(mode="after")
    def validate_content(self) -> IncomingMessageSchema:
        if self.role == "user":
            if self.content is None or not self.content.strip():
                raise ValueError("user content must not be empty")
            return self

        if self.content is not None and not self.content.strip():
            raise ValueError("assistant content must not be empty when provided")
        return self


class OutgoingMessageSchema(BaseModel):
    """Message returned to the client.

    Includes tool-related fields only on server-generated messages.
    """

    role: str = Field(..., description="Message role: user, assistant, or tool")
    content: str | None = Field(default=None, description="Text content")
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None, description="Tool calls from assistant"
    )
    tool_call_id: str | None = Field(default=None, description="Tool call ID for results")
    name: str | None = Field(default=None, description="Tool name for results")


class ChatRequest(BaseModel):
    """Request body for the chat endpoint.

    Attributes:
        messages: Full conversation history including the new user message.
            The last message should be the new user message.
    """

    messages: list[IncomingMessageSchema] = Field(
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
    parameters: dict[str, Any] = Field(..., description="Action parameters")
    preview: str = Field(..., description="Human-readable preview for HR")
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Redacted source and scope metadata used to create the draft",
    )
    confirm_endpoint: str = Field(..., description="Real API endpoint to call on confirm")
    confirm_method: str = Field(..., description="HTTP method (POST, PATCH, etc.)")
    confirm_body: dict[str, Any] = Field(..., description="Request body for the confirm endpoint")

    @field_validator("confirm_endpoint")
    @classmethod
    def endpoint_must_be_local_api(cls, v: str) -> str:
        if not v.startswith("/api/"):
            raise ValueError(
                "confirm_endpoint must start with /api/ — external URLs are not allowed"
            )
        return v


class DraftDecisionRequest(BaseModel):
    """HR decision for a Draft Action; the write remains outside the LLM loop."""

    decision: Literal["confirm", "reject"]
    action_type: str = Field(..., min_length=1, max_length=100)
    provenance: dict[str, Any] = Field(default_factory=dict)
    confirm_endpoint: str = Field(..., min_length=1, max_length=500)

    @field_validator("confirm_endpoint")
    @classmethod
    def endpoint_must_be_local_api(cls, v: str) -> str:
        if not v.startswith("/api/"):
            raise ValueError("confirm_endpoint must start with /api/")
        return v


class ChatResponseSchema(BaseModel):
    """Response from the chat endpoint.

    Attributes:
        messages: New messages added during this turn (assistant + tool results).
        draft_action: Optional Draft Action if a draft tool was invoked.
    """

    messages: list[OutgoingMessageSchema] = Field(
        ..., description="New messages from this assistant turn"
    )
    draft_action: DraftActionSchema | None = Field(
        default=None,
        description="Draft Action for HR to review (if a draft tool was called)",
    )
