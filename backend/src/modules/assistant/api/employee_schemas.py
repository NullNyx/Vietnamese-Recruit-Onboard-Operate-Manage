"""Pydantic schemas for the Employee Assistant API.

Reuses the same chat message and draft action shapes as the HR Assistant.
The only difference is auth (employee vs admin) and tool set.
"""

from __future__ import annotations

from src.modules.assistant.api.schemas import (
    ChatRequest,
    ChatResponseSchema,
    DraftActionSchema,
    IncomingMessageSchema,
    OutgoingMessageSchema,
)

__all__ = [
    "ChatRequest",
    "ChatResponseSchema",
    "DraftActionSchema",
    "IncomingMessageSchema",
    "OutgoingMessageSchema",
]
