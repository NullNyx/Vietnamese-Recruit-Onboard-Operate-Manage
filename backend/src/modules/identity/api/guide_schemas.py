"""Schemas for the Quick-Start Guide feature."""

from pydantic import BaseModel

ESSENTIAL_TASKS = [
    "google_workspace_connected",
    "ai_configured",
    "first_job_opening",
    "first_kb_document",
]

TASK_LABELS = {
    "google_workspace_connected": "Kết nối Google Workspace",
    "ai_configured": "Cấu hình AI",
    "first_job_opening": "Tạo Job Opening đầu tiên",
    "first_kb_document": "Upload tài liệu Knowledge Base",
}


class GuideTaskSchema(BaseModel):
    id: str
    label: str
    done: bool


class GuideProgressResponse(BaseModel):
    completed_tasks: list[str]
    dismissed: bool
    all_completed: bool
    progress: int  # 0-100
    tasks: list[GuideTaskSchema]


class UpdateGuideProgressRequest(BaseModel):
    completed_tasks: list[str] | None = None
    dismissed: bool | None = None
