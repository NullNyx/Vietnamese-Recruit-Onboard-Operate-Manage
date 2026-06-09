"""Domain entities for the AI Assistant module.

Defines the SQLModel table class for AssistantToolConfig — the runtime
toggle that lets admins enable/disable assistant tools without code changes.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class AssistantToolConfig(SQLModel, table=True):
    """Tracks whether a specific assistant tool is enabled.

    Each row corresponds to one ToolDefinition in domain/tools.py.
    The admin toggles tools via /api/admin/assistant-tools; the
    ToolRegistry reads enabled tools at chat time.

    Attributes:
        tool_name: Primary key, must match a name in TOOL_DEFINITIONS.
        enabled: Whether the tool is currently active. Defaults to True.
        updated_at: Timestamp of the last admin change.
    """

    __tablename__ = "assistant_tool_config"

    tool_name: str = Field(max_length=100, primary_key=True)
    enabled: bool = Field(default=True, nullable=False)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
