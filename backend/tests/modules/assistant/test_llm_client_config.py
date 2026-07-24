"""Regression tests for Assistant LLM client transport settings."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.assistant.infrastructure import llm_client
from src.modules.assistant.infrastructure.config import AssistantSettings


def test_llm_client_forwards_timeout_and_retry_policy(monkeypatch) -> None:
    """Configured retry limits must bound provider outage latency."""
    constructed: dict[str, object] = {}

    def fake_async_openai(**kwargs):
        constructed.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(llm_client, "AsyncOpenAI", fake_async_openai)

    llm_client.AssistantLLMClient(
        AssistantSettings(
            base_url="http://provider.invalid/v1",
            api_key="test",
            model="test-model",
            timeout_seconds=5,
            max_retries=0,
        )
    )

    assert constructed["timeout"] == 5
    assert constructed["max_retries"] == 0


@pytest.mark.asyncio
async def test_llm_client_parses_data_wrapped_provider_response() -> None:
    """OpenAI-compatible gateways may wrap choices under response.data."""
    client = llm_client.AssistantLLMClient.__new__(llm_client.AssistantLLMClient)
    client._model = "test-model"
    client._client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(
                    return_value=SimpleNamespace(
                        choices=None,
                        model_extra={
                            "data": {
                                "choices": [
                                    {
                                        "message": {
                                            "content": "OK",
                                            "tool_calls": [],
                                        }
                                    }
                                ]
                            }
                        },
                        usage=None,
                    )
                )
            )
        )
    )

    response = await client.chat([{"role": "user", "content": "Reply with OK"}])

    assert response.content == "OK"
    assert response.tool_calls == []
