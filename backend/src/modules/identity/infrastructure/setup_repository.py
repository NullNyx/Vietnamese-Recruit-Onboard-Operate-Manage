"""Repository for SystemSetup persistence."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.identity.domain.entities import SystemSetup


class SystemSetupRepository:
    """SQL-based repository for SystemSetup."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def get_setup_record(self) -> SystemSetup | None:
        """Get the single setup record.
        
        Returns:
            The SystemSetup record if it exists, None otherwise.
        """
        result = await self._session.execute(select(SystemSetup))
        return result.scalars().first()

    async def upsert_setup_record(self, record: SystemSetup) -> SystemSetup:
        """Upsert the setup record.
        
        Args:
            record: The SystemSetup record to save.
            
        Returns:
            The saved SystemSetup record.
        """
        existing = await self.get_setup_record()
        if existing:
            existing.is_setup_completed = record.is_setup_completed
            existing.setup_token = record.setup_token
            self._session.add(existing)
            return existing
        else:
            self._session.add(record)
            return record
