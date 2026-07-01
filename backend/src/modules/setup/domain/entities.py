"""Domain entities for the Setup module.

Tracks initial system setup progress and stores company/AI configuration
that is collected during the setup wizard before the dashboard is accessible.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class SetupState(SQLModel, table=True):
    """Single-row table tracking setup wizard completion and collected data.

    There is at most one row. ``completed_at`` being non-NULL means the
    setup wizard has finished. Additional fields store company profile
    and AI provider configuration for first-use convenience.

    Attributes:
        id: Primary key.
        completed_at: When the setup wizard was finished (NULL = not done).
        completed_by_user_id: The SUPER_ADMIN who completed the wizard.
        org_name: Company name entered during setup.
        org_tax_code: Company tax code entered during setup.
        org_timezone: IANA timezone for the company.
        ai_provider: AI provider type e.g. ``"openai"``, ``"disabled"``.
        ai_api_key_enc: Encrypted API key for the AI provider.
        created_at: Row creation timestamp.
        updated_at: Row update timestamp.
    """

    __tablename__ = "setup_state"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_by_user_id: UUID | None = Field(default=None, nullable=True)

    org_name: str | None = Field(default=None, max_length=255)
    org_tax_code: str | None = Field(default=None, max_length=20)
    org_timezone: str | None = Field(default=None, max_length=64)

    ai_provider: str | None = Field(default=None, max_length=50)
    ai_api_key_enc: str | None = Field(default=None, max_length=500)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
