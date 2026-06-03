"""Pydantic request/response schemas for the Admin API endpoints.

Defines data transfer objects for user management, role changes,
and audit log retrieval under /api/admin/*.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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


# --- Admin Organization Domain Schemas ---


class DomainListResponse(BaseModel):
    """Response schema for listing allowed Organization domains.

    Attributes:
        allowed_domains: The list of email domains permitted for login.
    """

    model_config = ConfigDict(from_attributes=True)

    allowed_domains: list[str]


class DomainAddRequest(BaseModel):
    """Request schema for adding domains to the allowed list.

    Attributes:
        domains: One or more bare domain strings (e.g. ``company.vn``).
    """

    domains: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of domain strings to add (e.g. company.vn)",
    )


class DomainReplaceRequest(BaseModel):
    """Request schema for replacing the entire allowed domain list.

    Attributes:
        domains: The new complete list of domain strings.
    """

    domains: list[str] = Field(
        ...,
        max_length=50,
        description="Complete list of domain strings to set",
    )


class DomainRemoveResponse(BaseModel):
    """Response schema after removing a domain.

    Attributes:
        removed: The domain that was removed.
        allowed_domains: The updated list of allowed domains.
    """

    removed: str
    allowed_domains: list[str]
