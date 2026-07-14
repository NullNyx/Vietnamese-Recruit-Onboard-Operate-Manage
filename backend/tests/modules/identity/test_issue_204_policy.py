from uuid import uuid4

import pytest

from src.modules.identity.application.organization_ai_config_service import (
    AIPolicyPreset,
    OrganizationAIConfigService,
    OrganizationAIConfigValidationError,
)
from src.modules.identity.domain.entities import OrganizationAIConfiguration, User
from src.modules.identity.infrastructure.config import AuthSettings
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils


class FakeRepository:
    def __init__(self) -> None:
        self.config: OrganizationAIConfiguration | None = None

    async def get(self) -> OrganizationAIConfiguration | None:
        return self.config

    async def save(self, config: OrganizationAIConfiguration) -> OrganizationAIConfiguration:
        self.config = config
        return config


@pytest.fixture
def service() -> OrganizationAIConfigService:
    crypto = CryptoUtils(__import__("base64").b64encode(b"x" * 32).decode())
    return OrganizationAIConfigService(
        FakeRepository(), crypto, AuthSettings.model_construct(ai_deployment_key=None)
    )


@pytest.mark.asyncio
async def test_capabilities_require_independent_consent(
    service: OrganizationAIConfigService,
) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    repository = service.repository
    await repository.save(
        OrganizationAIConfiguration(
            provider="openai",
            base_url="https://provider.example/v1",
            model="model",
            api_key_enc="enc",
        )
    )
    service._resolve_api_key = lambda config: _resolved_key()  # type: ignore[method-assign]
    service._test_completion = lambda base_url, api_key, model: _completed()  # type: ignore[method-assign]

    await service.accept_data_policy(user)
    with pytest.raises(OrganizationAIConfigValidationError, match="AI Automation consent"):
        await service.enable_automation(user)

    await service.accept_automation_consent(user)
    await service.enable_automation(user)
    with pytest.raises(OrganizationAIConfigValidationError, match="AI Assistant consent"):
        await service.enable_assistant(user)


@pytest.mark.asyncio
async def test_policy_preset_does_not_expose_threshold(
    service: OrganizationAIConfigService,
) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    await service.update_provider_config("openai", "https://provider.example/v1", "model", user)
    result = await service.set_policy_preset(AIPolicyPreset.CONSERVATIVE, user)

    assert result.view.ai_policy_preset == "conservative"
    assert result.view.ai_policy_preset_version == "conservative-v1"
    assert "threshold" not in str(result.audit_details).lower()


async def _resolved_key() -> str:
    return "secret"


async def _completed() -> None:
    return None
