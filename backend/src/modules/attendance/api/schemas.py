"""API schemas for Attendance network configuration."""

from datetime import datetime

from pydantic import BaseModel, Field


class NetworkAllowlistResponse(BaseModel):
    """Response schema for network allowlist."""

    networks: list[str] = Field(default_factory=list, description="List of CIDR notations")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class NetworkAllowlistUpdate(BaseModel):
    """Request schema for updating network allowlist."""

    networks: list[str] = Field(
        default_factory=list, description="List of CIDR notations to replace current allowlist"
    )


class NetworkAddRequest(BaseModel):
    """Request schema for adding CIDRs to allowlist."""

    networks: list[str] = Field(min_length=1, description="List of CIDR notations to add")


class NetworkRemoveRequest(BaseModel):
    """Request schema for removing CIDR from allowlist."""

    cidr: str = Field(description="CIDR notation to remove")
