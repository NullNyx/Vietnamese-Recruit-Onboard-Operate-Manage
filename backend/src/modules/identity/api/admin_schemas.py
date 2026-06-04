"""Pydantic request/response schemas for the Admin API endpoints.

Defines data transfer objects for user management, role changes,
and audit log retrieval under /api/admin/*.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.identity.domain.entities import AuditActionType, UserRole


class RoleUpdateRequest(BaseModel):
    """Request schema for PATCH /api/admin/users/{id}/role.

    Attributes:
        role: The new role to assign to the user. Must be \'admin\' or \'user\'.
    """

    role: UserRole


class AdminUserResponse(BaseModel):
    """Response schema for user entries in the admin user list.

    Attributes:
        id: The user\'s unique identifier.
        email: The user\'s email address.
        name: The user\'s display name.
        avatar_url: URL to the user\'s avatar image, if available.
        role: The user\'s current role.
        is_active: Whether the user account is active.
        created_at: When the user account was created.
        last_login: When the user last authenticated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    avatar_url: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: datetime


class AuditLogResponse(BaseModel):
    """Response schema for individual audit log entries.

    Attributes:
        id: The audit log entry\'s unique identifier.
        admin_email: Email of the admin who performed the action.
        action_type: The type of admin action recorded.
        details: Action-specific details (sensitive values masked).
        created_at: When the action was performed.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    admin_email: str
    action_type: AuditActionType
    details: dict
    created_at: datetime


class PaginatedAuditLogsResponse(BaseModel):
    """Response schema for paginated audit log queries.

    Attributes:
        items: The list of audit log entries for the current page.
        total: The total number of entries matching the query filters.
        page: The current page number (1-indexed).
        page_size: The number of entries per page.
    """

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int



class AssistantToolConfigResponse(BaseModel):
    """Response schema for a single assistant tool config entry.

    Attributes:
        tool_name: The tool's machine-readable name.
        description: Human-readable description for the LLM.
        kind: Tool kind (read or draft).
        enabled: Whether the tool is currently active.
        updated_at: When the tool config was last changed.
    """

    tool_name: str
    description: str
    kind: str
    enabled: bool
    updated_at: datetime | None = None


class AssistantToolConfigListResponse(BaseModel):
    """Response schema for the list of all assistant tool configs.

    Attributes:
        tools: All tools with their enabled status.
    """

    tools: list[AssistantToolConfigResponse]


class AssistantToolConfigUpdateRequest(BaseModel):
    """Request schema for PUT /api/admin/assistant-tools.

    Attributes:
        tools: Mapping of tool_name to enabled status.
    """

    tools: dict[str, bool]
