"""API schemas for onboarding template management."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

OnboardingTemplateType = Literal["task", "document", "contract"]


class OnboardingTemplateBase(BaseModel):
    template_type: OnboardingTemplateType
    key: str = Field(max_length=40)
    display_name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    template_body: str | None = None
    is_required: bool = True
    order_index: int = 0


class OnboardingTemplateCreateRequest(OnboardingTemplateBase):
    version: int = 1
    is_system: bool = False
    is_archived: bool = False


class OnboardingTemplateUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_required: bool | None = None
    order_index: int | None = None
    is_archived: bool | None = None


class OnboardingTemplateResponse(OnboardingTemplateBase):
    id: UUID
    version: int
    is_system: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class OnboardingTemplateListResponse(BaseModel):
    items: list[OnboardingTemplateResponse]


class OnboardingTemplatePreviewResponse(BaseModel):
    id: UUID
    template_type: OnboardingTemplateType
    preview: str


class OnboardingTemplateSeedRequest(BaseModel):
    templates: list[dict[str, Any]]
