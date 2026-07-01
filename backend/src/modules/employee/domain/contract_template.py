"""ContractTemplate domain entity.

Reusable template for generating Contract drafts.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class ContractTemplate(SQLModel, table=True):
    """A reusable template for generating Contract drafts.

    Has versioning. Status: active / archived.
    """

    __tablename__ = "contract_templates"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    version: int = Field(default=1, nullable=False)
    content: str = Field(nullable=False)
    file_path: str | None = Field(default=None)
    status: str = Field(default="active", max_length=20, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_by: UUID = Field(foreign_key="users.id", nullable=False)
