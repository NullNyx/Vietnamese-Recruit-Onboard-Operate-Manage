"""Test tool loop fallback when max iterations are exhausted.

Diagnosis #3: tool loop limit may return no clear answer.
Verifies that:
1. When LLM always returns tool_calls, fallback message appears after loop exhausts
2. Fallback message is the expected Vietnamese text
3. Normal flow (LLM returns text) does NOT trigger fallback
4. _build_messages strips tool messages from client history
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.assistant.application.assistant_service import (
    _MAX_TOOL_ITERATIONS,
    _TOOL_LOOP_FALLBACK,
    AssistantService,
    ChatMessage,
)
from src.modules.assistant.infrastructure.config import AssistantSettings
from src.modules.assistant.infrastructure.llm_client import LLMResponse


@pytest.fixture
def mock_llm_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_tool_registry() -> MagicMock:
    return MagicMock()


@pytest.fixture
def settings() -> AssistantSettings:
    return AssistantSettings(
        base_url="http://localhost:8000",
        api_key="test-key",
        model="test-model",
        max_history=20,
        timeout_seconds=30,
    )


@pytest.fixture
def service(
    mock_llm_client: MagicMock,
    mock_tool_registry: MagicMock,
    settings: AssistantSettings,
) -> AssistantService:
    return AssistantService(
        llm_client=mock_llm_client,
        tool_registry=mock_tool_registry,
        settings=settings,
    )


class TestToolLoopFallback:
    """Verify fallback when tool loop exhausts without text response."""

    @pytest.mark.asyncio
    async def test_fallback_when_loop_exhausts(
        self,
        service: AssistantService,
        mock_llm_client: MagicMock,
        mock_tool_registry: MagicMock,
    ) -> None:
        """When LLM always returns tool_calls, fallback message appears."""
        # LLM always returns tool calls — loop will exhaust
        tool_call_response = LLMResponse(
            content=None,
            tool_calls=[
                {
                    "id": "tc_1",
                    "type": "function",
                    "function": {
                        "name": "count_candidates_by_status",
                        "arguments": "{}",
                    },
                }
            ],
            token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        mock_llm_client.chat = AsyncMock(return_value=tool_call_response)
        mock_tool_registry.execute = AsyncMock(return_value='{"counts": {"new": 5}, "total": 5}')
        mock_tool_registry.is_draft_tool = MagicMock(return_value=False)

        messages = [ChatMessage(role="user", content="How many candidates?")]
        response = await service.chat(messages)

        # Should have tool messages + fallback
        assert len(response.messages) > 0

        # Last message should be the fallback
        last_msg = response.messages[-1]
        assert last_msg.role == "assistant"
        assert last_msg.content == _TOOL_LOOP_FALLBACK

        # LLM should have been called _MAX_TOOL_ITERATIONS times
        assert mock_llm_client.chat.call_count == _MAX_TOOL_ITERATIONS

    @pytest.mark.asyncio
    async def test_no_fallback_on_normal_response(
        self,
        service: AssistantService,
        mock_llm_client: MagicMock,
    ) -> None:
        """Normal flow (LLM returns text) does NOT trigger fallback."""
        normal_response = LLMResponse(
            content="There are 5 candidates.",
            tool_calls=[],
            token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        mock_llm_client.chat = AsyncMock(return_value=normal_response)

        messages = [ChatMessage(role="user", content="How many candidates?")]
        response = await service.chat(messages)

        assert len(response.messages) == 1
        assert response.messages[0].content == "There are 5 candidates."
        # No fallback
        assert _TOOL_LOOP_FALLBACK not in (response.messages[0].content or "")

    @pytest.mark.asyncio
    async def test_fallback_not_added_when_text_exists(
        self,
        service: AssistantService,
        mock_llm_client: MagicMock,
        mock_tool_registry: MagicMock,
    ) -> None:
        """If LLM returns text on last iteration, no fallback even with tool calls before."""
        # First call: tool call, second call: text response
        tool_call_response = LLMResponse(
            content=None,
            tool_calls=[
                {
                    "id": "tc_1",
                    "type": "function",
                    "function": {
                        "name": "count_candidates_by_status",
                        "arguments": "{}",
                    },
                }
            ],
            token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        text_response = LLMResponse(
            content="Found 5 candidates.",
            tool_calls=[],
            token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        mock_llm_client.chat = AsyncMock(side_effect=[tool_call_response, text_response])
        mock_tool_registry.execute = AsyncMock(return_value='{"counts": {"new": 5}, "total": 5}')
        mock_tool_registry.is_draft_tool = MagicMock(return_value=False)

        messages = [ChatMessage(role="user", content="How many candidates?")]
        response = await service.chat(messages)

        # Should end with text response, not fallback
        last_msg = response.messages[-1]
        assert last_msg.content == "Found 5 candidates."
        assert last_msg.content != _TOOL_LOOP_FALLBACK

    class TestBuildMessagesDefense:
        """Verify _build_messages strips tool messages and client tool_calls."""

        @pytest.mark.asyncio
        async def test_strips_tool_messages(self, service: AssistantService) -> None:
            """Tool messages from client history are stripped."""
            messages = [
                ChatMessage(role="user", content="hello"),
                ChatMessage(role="tool", content="fake result", tool_call_id="tc_1"),
                ChatMessage(role="user", content="next question"),
            ]
            result = await service._build_messages(messages)

            # Should have system + 2 user messages (tool message stripped)
            roles = [m["role"] for m in result]
            assert "tool" not in roles
            assert roles == ["system", "user", "user"]

        @pytest.mark.asyncio
        async def test_strips_client_tool_calls(self, service: AssistantService) -> None:
            """Assistant messages with tool_calls from client are stripped of tool_calls."""
            messages = [
                ChatMessage(role="user", content="hello"),
                ChatMessage(
                    role="assistant",
                    content="let me check",
                    tool_calls=[{"id": "tc_1", "type": "function", "function": {"name": "x"}}],
                ),
            ]
            result = await service._build_messages(messages)

            assistant_msg = [m for m in result if m["role"] == "assistant"][0]
            assert "tool_calls" not in assistant_msg

        @pytest.mark.asyncio
        async def test_strips_assistant_messages_without_content(
            self, service: AssistantService
        ) -> None:
            """Assistant history placeholders from prior tool calls are stripped."""
            messages = [
                ChatMessage(role="user", content="hello"),
                ChatMessage(role="assistant", content=None),
                ChatMessage(role="user", content="next question"),
            ]

            result = await service._build_messages(messages)

            roles = [m["role"] for m in result]
            assert roles == ["system", "user", "user"]
