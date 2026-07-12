"""Application service for safe Organization AI configuration updates."""

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from src.modules.identity.domain.entities import OrganizationAIConfiguration, User
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


@dataclass(frozen=True)
class AIConfigurationCandidate:
    provider: str
    base_url: str
    model: str
    api_key: str


class OrganizationAIConfigValidationError(Exception):
    pass


class OrganizationAIConfigTestError(Exception):
    pass


class OrganizationAIConfigService:
    def __init__(self, repository: OrganizationAIConfigRepository, crypto: CryptoUtils) -> None:
        self.repository = repository
        self.crypto = crypto

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
        if config is None:
            return AIConfigurationView(None, None, None, None, False, None)
        key = self.crypto.decrypt(config.api_key_enc)
        return AIConfigurationView(
            provider=config.provider,
            base_url=config.base_url,
            model=config.model,
            api_key_masked=self._mask_key(key),
            configured=True,
            updated_at=config.updated_at,
        )

    async def test_connection(self, candidate: AIConfigurationCandidate) -> None:
        self.validate(candidate)
        url = candidate.base_url.rstrip("/") + "/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url, headers={"Authorization": f"Bearer {candidate.api_key}"}
                )
        except httpx.HTTPError as exc:
            raise OrganizationAIConfigTestError(f"Unable to connect to provider: {exc}") from exc
        if response.status_code < 200 or response.status_code >= 300:
            raise OrganizationAIConfigTestError(
                f"Provider connection test failed with status {response.status_code}"
            )

    async def update(self, candidate: AIConfigurationCandidate, admin: User) -> AIConfigurationView:
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
        config.updated_at = now
        config.updated_by_user_id = admin.id
        await self.repository.save(config)
        return await self.get_view()
