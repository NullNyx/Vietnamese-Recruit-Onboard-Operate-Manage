from uuid import uuid4

import httpx
import pytest
import respx

from src.modules.identity.application.organization_ai_config_service import (
    AIConfigurationCandidate,
    AIConfigurationView,
    OrganizationAIConfigService,
    OrganizationAIConfigTestError,
    OrganizationAIConfigValidationError,
)
from src.modules.identity.domain.entities import CredentialSource, OrganizationAIConfiguration, User
from src.modules.identity.infrastructure.config import AuthSettings
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils


# Stub settings with configurable deployment key
class StubSettings(AuthSettings):
    model_config = {"env_prefix": "AUTH_", "extra": "allow"}

    google_client_id: str = "test-client-id"  # type: ignore[assignment]
    google_client_secret: str = "test-client-secret"  # type: ignore[assignment]
    jwt_secret_key: str = "test-jwt-secret"  # type: ignore[assignment]
    oauth_token_encryption_key: str = "dGVzdC1rZXktMzItYnl0ZXMteHh4eHh4eA=="  # type: ignore[assignment]

    ai_deployment_key: str | None = None  # type: ignore[assignment]


class FakeRepository:
    def __init__(self) -> None:
        self.config: OrganizationAIConfiguration | None = None

    async def get(self) -> OrganizationAIConfiguration | None:
        return self.config

    async def save(self, config: OrganizationAIConfiguration) -> OrganizationAIConfiguration:
        self.config = config
        return config


@pytest.fixture
def crypto() -> CryptoUtils:
    key = __import__("base64").b64encode(b"x" * 32).decode()
    return CryptoUtils(key)


@pytest.fixture
def service(crypto: CryptoUtils) -> OrganizationAIConfigService:
    return OrganizationAIConfigService(FakeRepository(), crypto, StubSettings())


@pytest.fixture
def service_with_deployment_key(crypto: CryptoUtils) -> OrganizationAIConfigService:
    settings = StubSettings()
    settings.ai_deployment_key = "sk-deployment-key-12345678"
    return OrganizationAIConfigService(FakeRepository(), crypto, settings)


# ---------------------------------------------------------------------------
# Existing tests adapted to new return type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_update_tests_before_encrypting_and_never_returns_plaintext(service: OrganizationAIConfigService) -> None:
    route = respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    user = User(id=uuid4(), email="hr@example.com", name="HR")

    result = await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "custom", "secret-key"),
        user,
    )

    assert route.called
    assert result.view.api_key_masked == "******-key"
    assert result.view.credential_source == CredentialSource.ORG_API_KEY.value
    assert result.audit_details["action"] == "update"
    assert service.repository.config is not None
    assert service.repository.config.api_key_enc != "secret-key"
    assert service.repository.config.credential_source == CredentialSource.ORG_API_KEY.value


@pytest.mark.asyncio
@respx.mock
async def test_failed_connection_does_not_replace_existing(service: OrganizationAIConfigService) -> None:
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(500, json={"error": "no"})
    )
    user = User(id=uuid4(), email="hr@example.com", name="HR")

    with pytest.raises(OrganizationAIConfigTestError):
        await service.update(
            AIConfigurationCandidate("openai", "https://api.example.test/v1", "custom", "secret-key"),
            user,
        )
    assert service.repository.config is None


# ---------------------------------------------------------------------------
# New tests: deployment key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_view_shows_deployment_key_unavailable(service: OrganizationAIConfigService) -> None:
    view = await service.get_view()
    assert view.deployment_key_available is False
    assert view.credential_source == CredentialSource.ORG_API_KEY.value


@pytest.mark.asyncio
async def test_get_view_shows_deployment_key_available(service_with_deployment_key: OrganizationAIConfigService) -> None:
    view = await service_with_deployment_key.get_view()
    assert view.deployment_key_available is True


@pytest.mark.asyncio
@respx.mock
async def test_set_credential_source_to_deployment_key(service_with_deployment_key: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    # First create a config
    route = respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await service_with_deployment_key.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "custom", "sk-test-key"),
        user,
    )
    route.reset()

    # Now switch to deployment key (mocking the deployment key test)
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    result = await service_with_deployment_key.set_credential_source(
        CredentialSource.DEPLOYMENT_KEY.value, user
    )
    assert result.view.credential_source == CredentialSource.DEPLOYMENT_KEY.value
    assert result.audit_details["action"] == "source_change"


@pytest.mark.asyncio
@respx.mock
async def test_set_credential_source_to_deployment_key_fails_when_not_available(
    service: OrganizationAIConfigService,
) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "custom", "sk-test-key"),
        user,
    )

    with pytest.raises(OrganizationAIConfigValidationError, match="Deployment key is not configured"):
        await service.set_credential_source(CredentialSource.DEPLOYMENT_KEY.value, user)


# ---------------------------------------------------------------------------
# Rotation (activate) tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_activate_org_api_key(service: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "custom", "old-key"),
        user,
    )

    old_enc = service.repository.config.api_key_enc

    result = await service.activate_org_api_key("sk-new-key", user)
    assert result.view.api_key_masked is not None
    assert result.audit_details["action"] == "rotate"
    assert result.audit_details["key_updated"] is True
    assert service.repository.config.api_key_enc != old_enc
    assert service.repository.config.credential_source == CredentialSource.ORG_API_KEY.value


@pytest.mark.asyncio
async def test_activate_without_config_fails(service: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    with pytest.raises(OrganizationAIConfigValidationError, match="No provider configuration"):
        await service.activate_org_api_key("sk-new-key", user)


# ---------------------------------------------------------------------------
# Revoke tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_revoke_org_api_key_clears_key_preserves_config(service: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "gpt-4o", "sk-key"),
        user,
    )

    result = await service.revoke_org_api_key(user)

    assert result.view.api_key_masked is None
    assert result.view.provider == "openai"
    assert result.view.model == "gpt-4o"
    assert result.view.configured is True
    assert result.audit_details["action"] == "revoke"
    assert service.repository.config.api_key_enc == ""
    assert service.repository.config.provider == "openai"
    assert service.repository.config.model == "gpt-4o"


@pytest.mark.asyncio
async def test_revoke_without_config_fails(service: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    with pytest.raises(OrganizationAIConfigValidationError, match="No provider configuration"):
        await service.revoke_org_api_key(user)


# ---------------------------------------------------------------------------
# Audit safety: no secrets in audit details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_update_audit_has_no_secret(service: OrganizationAIConfigService) -> None:
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    user = User(id=uuid4(), email="hr@example.com", name="HR")

    result = await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "gpt-4o", "sk-secret-12345"),
        user,
    )
    details = result.audit_details
    assert "provider" in details
    assert "base_url" in details
    assert "model" in details
    # Must NOT contain the actual secret key value
    assert "sk-secret-12345" not in str(details)
    # The details dict must not have a raw api_key field
    assert "api_key" not in details


@pytest.mark.asyncio
@respx.mock
async def test_rotate_audit_has_no_secret(service: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "gpt-4o", "old-key"),
        user,
    )

    result = await service.activate_org_api_key("sk-new-secret-key", user)
    assert "sk-new-secret-key" not in str(result.audit_details)


@pytest.mark.asyncio
@respx.mock
async def test_revoke_audit_has_no_secret(service: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "gpt-4o", "sk-key"),
        user,
    )

    result = await service.revoke_org_api_key(user)
    assert "sk-key" not in str(result.audit_details)


# ---------------------------------------------------------------------------
# Provider config update without key change
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_update_provider_config_preserves_key(service: OrganizationAIConfigService) -> None:
    user = User(id=uuid4(), email="hr@example.com", name="HR")
    respx.get("https://api.example.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await service.update(
        AIConfigurationCandidate("openai", "https://api.example.test/v1", "gpt-4o", "sk-key"),
        user,
    )
    old_enc = service.repository.config.api_key_enc

    result = await service.update_provider_config(
        "anthropic", "https://api.anthropic.com/v1", "claude-3.5", user
    )
    assert result.view.provider == "anthropic"
    assert result.view.model == "claude-3.5"
    assert service.repository.config.api_key_enc == old_enc
    assert result.audit_details["action"] == "update_provider"
