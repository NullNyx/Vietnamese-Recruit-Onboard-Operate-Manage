"""Repository for assistant tool configuration persistence.

Reads and writes the assistant_tool_config table that controls which
tools are enabled for the AI Assistant.

Uses SQLAlchemy execute() pattern consistent with the rest of the codebase.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.modules.assistant.domain.entities import AssistantToolConfig


class ToolConfigRepository:
    """CRUD for AssistantToolConfig rows.

    Args:
        session: Async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[AssistantToolConfig]:
        """Return all tool config rows, ordered by tool_name."""
        statement = select(AssistantToolConfig).order_by(col(AssistantToolConfig.tool_name))
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_enabled_tool_names(self) -> set[str]:
        """Return the set of tool_name values where enabled=True."""
        statement = select(AssistantToolConfig.tool_name).where(
            AssistantToolConfig.enabled == True  # noqa: E712
        )
        result = await self._session.execute(statement)
        return set(result.scalars().all())

    async def upsert_many(self, configs: dict[str, bool]) -> None:
        """Batch upsert tool configs.

        For each tool_name in configs:
        - If row exists: update enabled + updated_at
        - If row does not exist: insert with the given enabled value

        Args:
            configs: Mapping of tool_name -> enabled.
        """
        now = datetime.now(UTC)
        for tool_name, enabled in configs.items():
            existing = await self._session.get(AssistantToolConfig, tool_name)
            if existing:
                existing.enabled = enabled
                existing.updated_at = now
            else:
                self._session.add(
                    AssistantToolConfig(
                        tool_name=tool_name,
                        enabled=enabled,
                        updated_at=now,
                    )
                )
        await self._session.commit()
