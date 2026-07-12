from uuid import uuid4

import httpx
import pytest
import respx

from src.modules.identity.application.organization_ai_config_service import (
    AIConfigurationCandidate,
    OrganizationAIConfigService,
    OrganizationAIConfigTestError,
)
from src.modules.identity.domain.entities import User
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils


class FakeRepository:
    def __init__(self) -> None:
        self.config = None

    async def get(self):
        return self.config

    async def save(self, config):
        self.config = config
        return config


@pytest.fixture
def service() -> OrganizationAIConfigService:
    key = __import__("base64").b64encode(b"x" * 32).decode()
    return OrganizationAIConfigService(FakeRepository(), CryptoUtils(key))


@pytest.mark.asyncio
@respx.mock
async def test_update_tests_before_encrypting_and_never_returns_plaintext(service):
    route = respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    user = User(id=uuid4(), email="hr@example.com", name="HR")

    view = await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "custom", "secret-key"),
        user,
    )

    assert route.called
    assert view.api_key_masked == "******-key"
    assert service.repository.config.api_key_enc != "secret-key"


@pytest.mark.asyncio
@respx.mock
async def test_failed_connection_does_not_replace_existing(service):
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(500, json={"error": "no"})
    )
    user = User(id=uuid4(), email="hr@example.com", name="HR")

    with pytest.raises(OrganizationAIConfigTestError):
        await service.update(
            AIConfigurationCandidate(
                "openai", "https://api.example.test/v1", "custom", "secret-key"
            ),
            user,
        )
    assert service.repository.config is None
