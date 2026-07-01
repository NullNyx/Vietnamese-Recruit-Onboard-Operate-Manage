"""Pydantic schemas for the Setup wizard API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SetupStatusResponse(BaseModel):
    """Current setup wizard status."""

    setup_complete: bool
    admin_exists: bool
    org_configured: bool
    ai_provider_configured: bool


class CreateAdminRequest(BaseModel):
    """Create first administrator account."""

    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(max_length=255)


class OrgConfigRequest(BaseModel):
    """Company information."""

    name: str = Field(max_length=255)
    tax_code: str = Field(max_length=20)
    timezone: str = Field(max_length=64, default="Asia/Ho_Chi_Minh")


class AiProviderRequest(BaseModel):
    """AI provider configuration."""

    provider: str = Field(max_length=50)
    api_key: str | None = Field(default=None, max_length=500)


class SetupCompleteResponse(BaseModel):
    """Setup finalized confirmation."""

    status: str
