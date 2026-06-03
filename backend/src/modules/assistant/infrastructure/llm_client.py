"""LLM Client for the AI Assistant module.

Own AsyncOpenAI client built for tool-calling (ADR-0007).
Shares only configuration (endpoint, API key, model) with recruitment's
LLMAdapter — not code. The two clients are intentionally separate.

Features:
- Tool-calling loop: pass tool definitions, handle tool_calls, iterate
- Configurable max history (20 messages per grill decision)
- Token usage tracking
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from src.modules.assistant.infrastructure.config import AssistantSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    """Result from the LLM including content and tool calls.

    Attributes:
        content: Text content from the assistant (may be None if only tool calls).
        tool_calls: List of tool call dicts from the LLM.
        token_usage: Token usage statistics.
    """

    content: str | None
    tool_calls: list[dict]
    token_usage: dict[str, int]


class AssistantLLMClient:
    """LLM client for the AI Assistant, built for tool-calling.

    Args:
        settings: AssistantSettings with LLM connection details.
    """

    def __init__(self, settings: AssistantSettings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key or "not-needed",
            timeout=settings.timeout_seconds,
        )
        self._model = settings.model

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request with optional tool definitions.

        Args:
            messages: Full message history (system + user + assistant + tool results).
            tools: Optional tool definitions in OpenAI format.

        Returns:
            LLMResponse with content and/or tool_calls.

        Raises:
            ConnectionError: If the LLM endpoint is unreachable.
        """
        kwargs: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.3,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await self._client.chat.completions.create(**kwargs)
        except APITimeoutError as exc:
            logger.error("LLM request timed out: %s", exc)
            raise ConnectionError(f"LLM timeout: {exc}") from exc
        except APIConnectionError as exc:
            logger.error("LLM connection failed: %s", exc)
            raise ConnectionError(f"LLM connection failed: {exc}") from exc
        except APIStatusError as exc:
            logger.error("LLM API error: %s", exc)
            raise ConnectionError(f"LLM API error {exc.status_code}: {exc}") from exc

        choice = response.choices[0]
        message = choice.message

        tool_calls: list[dict] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )

        token_usage = self._extract_token_usage(response)

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            token_usage=token_usage,
        )

    @staticmethod
    def _extract_token_usage(response: object) -> dict[str, int]:
        """Extract token usage from the API response."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "total_tokens": getattr(usage, "total_tokens", 0) or 0,
        }
