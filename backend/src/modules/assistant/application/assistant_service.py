"""Assistant Service — orchestrates the tool-calling loop.

This is the core of the AI Assistant. It:
1. Receives user message + full conversation history
2. Trims to max_history messages (20, per grill decision)
3. Sends to LLM with tool definitions
4. If LLM returns tool_calls → execute tools → send results back → loop
5. If LLM returns text → return final response to frontend

The tool-calling loop continues until the LLM returns text without
tool_calls, or max iterations are reached (safety cap).
"""

from __future__ import annotations

import json
import logging
import typing
from dataclasses import dataclass
from typing import Any

from src.modules.assistant.application.tool_registry import ToolRegistry
from src.modules.assistant.domain.tools import get_openai_tools
from src.modules.assistant.infrastructure.config import AssistantSettings
from src.modules.assistant.infrastructure.llm_client import AssistantLLMClient

logger = logging.getLogger(__name__)

# Safety cap to prevent infinite tool-calling loops
_MAX_TOOL_ITERATIONS = 5

_SYSTEM_PROMPT = """You are the AI Assistant for Vroom HR, a Vietnamese HR management platform.

You help HR administrators with recruitment and onboarding data.
You speak Vietnamese when the user speaks Vietnamese, English otherwise.

You have access to these tools:
1. count_candidates_by_status — Count candidates in the pipeline by status
2. list_in_progress_onboarding — List onboarding processes currently in progress
3. search_candidates — Search for candidates by name or email
4. draft_interview_invitation — Draft an interview invitation for a candidate
5. draft_congratulations_email — Draft a congratulations/offer email for a candidate

Rules:
- You NEVER write to the database directly.
- You only propose actions for HR to confirm (human-in-the-loop).
- For Read-Tools: call them to answer data questions accurately.
- For Draft-Tools: Before calling the tool, ensure you have gathered all required
  parameters (time, location, position, etc.) from the user. If missing, politely
  ask the user for them.
- Be concise and helpful. Use Vietnamese when the user does.
- If a tool fails, tell the user clearly and suggest they try again.
"""


@dataclass
class ChatMessage:
    """A single message in the conversation.

    Attributes:
        role: Message role (user, assistant, tool).
        content: Text content.
        tool_calls: Optional tool calls from the assistant.
        tool_call_id: Optional ID linking a tool result to its call.
        name: Optional tool name for tool result messages.
        draft_action: Optional Draft Action from a draft tool.
    """

    role: str
    content: str | None = None
    tool_calls: list[dict[str, typing.Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    draft_action: dict[str, typing.Any] | None = None


@dataclass
class ChatResponse:
    """Response from the assistant chat endpoint.

    Attributes:
        messages: Updated conversation messages.
        draft_action: Optional Draft Action if a draft tool was called.
    """

    messages: list[ChatMessage]
    draft_action: dict[str, typing.Any] | None = None


class AssistantService:
    """Orchestrates the AI Assistant conversation loop.

    Args:
        llm_client: The assistant's own LLM client (ADR-0007).
        tool_registry: Tool executor for Read-Tools and Draft-Tools.
        settings: Assistant settings with max_history, etc.
    """

    def __init__(
        self,
        llm_client: AssistantLLMClient,
        tool_registry: ToolRegistry,
        settings: AssistantSettings,
    ) -> None:
        self._llm_client = llm_client
        self._tool_registry = tool_registry
        self._settings = settings

    async def chat(
        self,
        messages: list[ChatMessage],
        enabled_tool_names: set[str] | None = None,
    ) -> ChatResponse:
        """Process a user message through the tool-calling loop.

        Args:
            messages: Full conversation history including the new user message.
            enabled_tool_names: If provided, only these tools are sent to the LLM.

        Returns:
            ChatResponse with updated messages and optional draft_action.
        """
        # Build OpenAI-format messages with system prompt
        openai_messages = self._build_messages(messages)

        draft_action: dict[str, typing.Any] | None = None
        all_new_messages: list[ChatMessage] = []

        # Tool-calling loop
        for _iteration in range(_MAX_TOOL_ITERATIONS):
            response = await self._llm_client.chat(
                messages=openai_messages,
                tools=get_openai_tools(enabled_tool_names),
            )

            # No tool calls → LLM is done, return text response
            if not response.tool_calls:
                assistant_msg = ChatMessage(
                    role="assistant",
                    content=response.content or "",
                )
                all_new_messages.append(assistant_msg)
                break

            # Has tool calls → execute tools, add results, loop
            assistant_msg = ChatMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            all_new_messages.append(assistant_msg)

            # Add assistant message to context for the next LLM call
            assistant_openai: dict[str, Any] = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": response.tool_calls,
            }
            openai_messages.append(assistant_openai)

            # Execute each tool call
            for tc in response.tool_calls:
                tool_name = tc["function"]["name"]
                try:
                    tool_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    tool_args = {}

                result_str = await self._tool_registry.execute(tool_name, tool_args)

                # Check if this is a draft tool → extract Draft Action
                if self._tool_registry.is_draft_tool(tool_name):
                    try:
                        result_data = json.loads(result_str)
                        if "draft_action" in result_data:
                            draft_action = result_data["draft_action"]
                    except json.JSONDecodeError:
                        pass

                # Add tool result to messages
                tool_msg = ChatMessage(
                    role="tool",
                    content=result_str,
                    tool_call_id=tc["id"],
                    name=tool_name,
                )
                all_new_messages.append(tool_msg)

                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_str,
                    }
                )

        return ChatResponse(
            messages=all_new_messages,
            draft_action=draft_action,
        )

    def _build_messages(self, messages: list[ChatMessage]) -> list[dict[str, typing.Any]]:
        """Build OpenAI-format messages with system prompt and history trimming.

        Applies max_history limit per grill decision (20 messages).
        """
        result: list[dict[str, Any]] = [{"role": "system", "content": _SYSTEM_PROMPT}]

        # Trim to max_history (excluding system message)
        history = messages[-self._settings.max_history :]

        for msg in history:
            entry: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                entry["content"] = msg.content
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.name:
                entry["name"] = msg.name
            result.append(entry)

        return result
