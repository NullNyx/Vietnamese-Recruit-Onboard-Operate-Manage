"""Application service for safe Organization AI configuration updates."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from src.modules.identity.domain.entities import CredentialSource, OrganizationAIConfiguration, User
from src.modules.identity.infrastructure.config import AuthSettings
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils
from src.modules.identity.infrastructure.organization_ai_config_repository import (
    OrganizationAIConfigRepository,
)


@dataclass(frozen=True)
class AIConfigurationView:
    provider: str | None
    base_url: str | None
    model: str | None
    api_key_masked: str | None
    configured: bool
    updated_at: datetime | None
    credential_source: str = CredentialSource.ORG_API_KEY.value
    deployment_key_available: bool = False


@dataclass(frozen=True)
class AIConfigurationCandidate:
    provider: str
    base_url: str
    model: str
    api_key: str


@dataclass
class AIConfigurationUpdateResult:
    view: AIConfigurationView
    audit_details: dict[str, object] = field(default_factory=dict)


class OrganizationAIConfigValidationError(Exception):
    pass


class OrganizationAIConfigTestError(Exception):
    pass


class OrganizationAIConfigService:
    def __init__(
        self,
        repository: OrganizationAIConfigRepository,
        crypto: CryptoUtils,
        settings: AuthSettings | None = None,
    ) -> None:
        self.repository = repository
        self.crypto = crypto
        self._settings = settings

    def _get_settings(self) -> AuthSettings:
        if self._settings is not None:
            return self._settings
        from src.modules.identity.container import get_settings
        return get_settings()

    def _get_deployment_key(self) -> str | None:
        """Return the deployment key from settings if configured, else None."""
        key = self._get_settings().ai_deployment_key
        if not key or not key.strip():
            return None
        return key

    @staticmethod
    def validate(candidate: AIConfigurationCandidate) -> None:
        if not candidate.provider.strip():
            raise OrganizationAIConfigValidationError("provider must not be empty")
        parsed = urlparse(candidate.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise OrganizationAIConfigValidationError("base_url must be a valid HTTP(S) URL")
        if not candidate.model.strip():
            raise OrganizationAIConfigValidationError("model must not be empty")
        if not candidate.api_key.strip():
            raise OrganizationAIConfigValidationError("api_key must not be empty")

    @staticmethod
    def _mask_key(key: str) -> str:
        return "*" * (len(key) - 4) + key[-4:] if len(key) > 4 else "*" * len(key)

    async def get_view(self) -> AIConfigurationView:
        config = await self.repository.get()
        deployment_key = self._get_deployment_key()
        if config is None:
            return AIConfigurationView(
                None, None, None, None, False, None,
                deployment_key_available=deployment_key is not None,
            )
        params: dict[str, object] = dict(
            provider=config.provider,
            base_url=config.base_url,
            model=config.model,
            configured=True,
            updated_at=config.updated_at,
            credential_source=config.credential_source,
            deployment_key_available=deployment_key is not None,
        )
        if config.credential_source == CredentialSource.DEPLOYMENT_KEY.value:
            params["api_key_masked"] = "****" if deployment_key else None
        elif config.api_key_enc:
            try:
                key = self.crypto.decrypt(config.api_key_enc)
                params["api_key_masked"] = self._mask_key(key)
            except Exception:
                params["api_key_masked"] = None
        else:
            params["api_key_masked"] = None
        return AIConfigurationView(**params)  # type: ignore[arg-type]

    async def _test_url(self, base_url: str, api_key: str) -> None:
        """Test connectivity to the provider's /models endpoint."""
        url = base_url.rstrip("/") + "/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url, headers={"Authorization": f"Bearer {api_key}"}
                )
        except httpx.HTTPError as exc:
            raise OrganizationAIConfigTestError(f"Unable to connect to provider: {exc}") from exc
        if response.status_code < 200 or response.status_code >= 300:
            raise OrganizationAIConfigTestError(
                f"Provider connection test failed with status {response.status_code}"
            )

    async def test_connection(self, candidate: AIConfigurationCandidate) -> None:
        self.validate(candidate)
        await self._test_url(candidate.base_url, candidate.api_key)

    async def test_deployment_key_connection(
        self, provider: str, base_url: str, model: str
    ) -> None:
        """Test connectivity using the deployment-wide key."""
        deployment_key = self._get_deployment_key()
        if not deployment_key:
            raise OrganizationAIConfigTestError("No deployment key is configured")
        candidate = AIConfigurationCandidate(
            provider=provider,
            base_url=base_url,
            model=model,
            api_key=deployment_key,
        )
        self.validate(candidate)
        await self._test_url(base_url, deployment_key)

    async def _resolve_api_key(self, config: OrganizationAIConfiguration) -> str:
        """Return the actual API key for a config based on its credential source."""
        if config.credential_source == CredentialSource.DEPLOYMENT_KEY.value:
            key = self._get_deployment_key()
            if not key:
                raise OrganizationAIConfigValidationError(
                    "Deployment key is not available"
                )
            return key
        if not config.api_key_enc:
            raise OrganizationAIConfigValidationError(
                "Organization API key is revoked or not configured"
            )
        return self.crypto.decrypt(config.api_key_enc)

    async def update(
        self, candidate: AIConfigurationCandidate, admin: User
    ) -> AIConfigurationUpdateResult:
        """Test connection and update provider + model + org API key atomically."""
        await self.test_connection(candidate)
        encrypted = self.crypto.encrypt(candidate.api_key)
        now = datetime.now(UTC)
        existing = await self.repository.get()
        config = existing or OrganizationAIConfiguration(
            id=uuid4(), organization_singleton_key="default", created_at=now
        )
        config.provider = candidate.provider.strip()
        config.base_url = candidate.base_url.rstrip("/")
        config.model = candidate.model.strip()
        config.api_key_enc = encrypted
        config.credential_source = CredentialSource.ORG_API_KEY.value
        config.updated_at = now
        config.updated_by_user_id = admin.id
        await self.repository.save(config)
        return AIConfigurationUpdateResult(
            view=await self.get_view(),
            audit_details={
                "provider": candidate.provider.strip(),
                "base_url": candidate.base_url.rstrip("/"),
                "model": candidate.model.strip(),
                "credential_source": CredentialSource.ORG_API_KEY.value,
                "action": "update",
            },
        )

    async def activate_org_api_key(
        self, api_key: str, admin: User
    ) -> AIConfigurationUpdateResult:
        """Activate a new Organization API key (saves encrypted key). No test performed."""
        config = await self.repository.get()
        if config is None:
            raise OrganizationAIConfigValidationError(
                "No provider configuration exists. Use update to create one."
            )
        if not api_key.strip():
            raise OrganizationAIConfigValidationError("api_key must not be empty")
        encrypted = self.crypto.encrypt(api_key.strip())
        now = datetime.now(UTC)
        config.api_key_enc = encrypted
        config.credential_source = CredentialSource.ORG_API_KEY.value
        config.updated_at = now
        config.updated_by_user_id = admin.id
        await self.repository.save(config)
        return AIConfigurationUpdateResult(
            view=await self.get_view(),
            audit_details={
                "provider": config.provider,
                "model": config.model,
                "credential_source": CredentialSource.ORG_API_KEY.value,
                "action": "rotate",
                "key_updated": True,
            },
        )

    async def set_credential_source(
        self, source: str, admin: User
    ) -> AIConfigurationUpdateResult:
        """Change the credential source (org_api_key or deployment_key)."""
        if source not in {s.value for s in CredentialSource}:
            raise OrganizationAIConfigValidationError(
                f"Invalid credential source: {source}"
            )
        config = await self.repository.get()
        if config is None:
            raise OrganizationAIConfigValidationError(
                "No provider configuration exists."
            )
        if source == CredentialSource.DEPLOYMENT_KEY.value:
            deployment_key = self._get_deployment_key()
            if not deployment_key:
                raise OrganizationAIConfigValidationError(
                    "Deployment key is not configured. Set AI_DEPLOYMENT_KEY environment variable."
                )
            # Test with deployment key
            await self._test_url(config.base_url, deployment_key)
        elif source == CredentialSource.ORG_API_KEY.value:
            if not config.api_key_enc:
                raise OrganizationAIConfigValidationError(
                    "No Organization API key is configured. Use update to set one."
                )
        now = datetime.now(UTC)
        config.credential_source = source
        config.updated_at = now
        config.updated_by_user_id = admin.id
        await self.repository.save(config)
        return AIConfigurationUpdateResult(
            view=await self.get_view(),
            audit_details={
                "credential_source": source,
                "action": "source_change",
            },
        )

    async def revoke_org_api_key(self, admin: User) -> AIConfigurationUpdateResult:
        """Revoke the Organization API key, preserving provider/model configuration."""
        config = await self.repository.get()
        if config is None:
            raise OrganizationAIConfigValidationError(
                "No provider configuration exists."
            )
        now = datetime.now(UTC)
        config.api_key_enc = ""
        config.credential_source = CredentialSource.ORG_API_KEY.value
        config.updated_at = now
        config.updated_by_user_id = admin.id
        await self.repository.save(config)
        return AIConfigurationUpdateResult(
            view=await self.get_view(),
            audit_details={
                "provider": config.provider,
                "model": config.model,
                "action": "revoke",
            },
        )

    async def update_provider_config(
        self, provider: str, base_url: str, model: str, admin: User
    ) -> AIConfigurationUpdateResult:
        """Update provider/model/base_url without changing the API key."""
        from urllib.parse import urlparse

        if not provider.strip():
            raise OrganizationAIConfigValidationError("provider must not be empty")
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise OrganizationAIConfigValidationError("base_url must be a valid HTTP(S) URL")
        if not model.strip():
            raise OrganizationAIConfigValidationError("model must not be empty")

        existing = await self.repository.get()
        now = datetime.now(UTC)
        config = existing or OrganizationAIConfiguration(
            id=uuid4(), organization_singleton_key="default", created_at=now
        )
        config.provider = provider.strip()
        config.base_url = base_url.rstrip("/")
        config.model = model.strip()
        if existing is None:
            config.api_key_enc = ""
        config.updated_at = now
        config.updated_by_user_id = admin.id
        await self.repository.save(config)
        return AIConfigurationUpdateResult(
            view=await self.get_view(),
            audit_details={
                "provider": provider.strip(),
                "base_url": base_url.rstrip("/"),
                "model": model.strip(),
                "action": "update_provider",
            },
        )
