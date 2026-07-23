"""FastAPI router for the Quick-Start Guide."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.api.guide_schemas import (
    ESSENTIAL_TASKS,
    TASK_LABELS,
    GuideProgressResponse,
    GuideTaskSchema,
    UpdateGuideProgressRequest,
)
from src.modules.identity.container import get_db_session
from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)

guide_router = APIRouter(prefix="/api/guide", tags=["guide"])


def _build_response(progress: dict) -> GuideProgressResponse:
    completed = progress.get("completed_tasks", [])
    dismissed = progress.get("dismissed", False)
    all_completed = all(t in completed for t in ESSENTIAL_TASKS)
    progress_pct = int((len(completed) / len(ESSENTIAL_TASKS)) * 100) if ESSENTIAL_TASKS else 100
    tasks = [
        GuideTaskSchema(id=t, label=TASK_LABELS.get(t, t), done=t in completed)
        for t in ESSENTIAL_TASKS
    ]
    return GuideProgressResponse(
        completed_tasks=completed,
        dismissed=dismissed,
        all_completed=all_completed,
        progress=progress_pct,
        tasks=tasks,
    )


@guide_router.get("/progress", response_model=GuideProgressResponse)
async def get_guide_progress(
    session: AsyncSession = Depends(get_db_session),
) -> GuideProgressResponse:
    """Return the current guide progress state."""
    repo = OrganizationSettingsRepository(session)
    progress = await repo.get_guide_progress()
    return _build_response(progress)


@guide_router.patch("/progress", response_model=GuideProgressResponse)
async def update_guide_progress(
    body: UpdateGuideProgressRequest,
    session: AsyncSession = Depends(get_db_session),
) -> GuideProgressResponse:
    """Update guide progress—mark tasks done or dismiss."""
    repo = OrganizationSettingsRepository(session)
    updates: dict = {}
    if body.completed_tasks is not None:
        current = await repo.get_guide_progress()
        existing = set(current.get("completed_tasks", []))
        existing.update(body.completed_tasks)
        updates["completed_tasks"] = list(existing)
    if body.dismissed is not None:
        updates["dismissed"] = body.dismissed
    progress = await repo.update_guide_progress(updates)
    return _build_response(progress)
