"""Service for auto-detecting guide task completion."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)


async def mark_task_completed(session: AsyncSession, task_id: str) -> None:
    """Mark an essential setup task as completed (auto-detect)."""
    repo = OrganizationSettingsRepository(session)
    progress = await repo.get_guide_progress()
    completed = set(progress.get("completed_tasks", []))
    if task_id not in completed:
        completed.add(task_id)
        await repo.update_guide_progress({"completed_tasks": list(completed)})
