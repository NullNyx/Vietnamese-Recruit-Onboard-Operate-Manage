"""Persistence for the singleton Organization AI configuration."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.identity.domain.entities import OrganizationAIConfiguration


class OrganizationAIConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> OrganizationAIConfiguration | None:
        result = await self.session.execute(
            select(OrganizationAIConfiguration).where(
                OrganizationAIConfiguration.organization_singleton_key == "default"
            )
        )
        return result.scalars().first()

    async def save(self, config: OrganizationAIConfiguration) -> OrganizationAIConfiguration:
        existing = await self.get()
        if existing is not None and existing.id != config.id:
            existing.provider = config.provider
            existing.base_url = config.base_url
            existing.model = config.model
            existing.api_key_enc = config.api_key_enc
            existing.updated_at = config.updated_at
            existing.updated_by_user_id = config.updated_by_user_id
            self.session.add(existing)
            await self.session.flush()
            return existing
        self.session.add(config)
        await self.session.flush()
        return config
