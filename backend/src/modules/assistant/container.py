"""Dependency injection container for the AI Assistant module.

Wires together the AssistantService with its dependencies:
- AssistantLLMClient (own client, ADR-0007)
- ToolRegistry (reads from recruitment + onboarding services)
- AssistantSettings (ASSISTANT_LLM_* env vars)

Dependency direction is one-way (ADR-0004):
assistant/ depends on recruitment/ and onboarding/ services,
but no module depends on assistant/.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from src.modules.assistant.application.assistant_service import AssistantService
from src.modules.assistant.application.tool_registry import ToolRegistry
from src.modules.assistant.infrastructure.config import AssistantSettings
from src.modules.assistant.infrastructure.llm_client import AssistantLLMClient
from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.container import get_onboarding_service
from src.modules.recruitment.application.candidate_service import CandidateService
from src.modules.recruitment.container import get_candidate_service

# ---------------------------------------------------------------------------
# Settings & LLM Client (singletons)
# ---------------------------------------------------------------------------

@lru_cache
def get_assistant_settings() -> AssistantSettings:
    """Load and cache AssistantSettings from ASSISTANT_LLM_* env vars."""
    return AssistantSettings()


@lru_cache
def get_assistant_llm_client() -> AssistantLLMClient:
    """Create and cache the assistant's own LLM client (ADR-0007)."""
    settings = get_assistant_settings()
    return AssistantLLMClient(settings)


# ---------------------------------------------------------------------------
# FastAPI Depends providers
# ---------------------------------------------------------------------------

async def get_tool_registry(
    candidate_service: CandidateService = Depends(get_candidate_service),
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> ToolRegistry:
    """Provide a ToolRegistry wired to recruitment + onboarding services.

    Read-only dependency on other modules' services (ADR-0004).
    """
    return ToolRegistry(
        candidate_service=candidate_service,
        onboarding_service=onboarding_service,
    )


async def get_assistant_service(
    tool_registry: ToolRegistry = Depends(get_tool_registry),
) -> AssistantService:
    """Provide an AssistantService for the current request.

    Assembles the LLM client, tool registry, and settings into
    the orchestration service.
    """
    llm_client = get_assistant_llm_client()
    settings = get_assistant_settings()
    return AssistantService(
        llm_client=llm_client,
        tool_registry=tool_registry,
        settings=settings,
    )
