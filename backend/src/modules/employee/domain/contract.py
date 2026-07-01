"""Contract domain entity.

Legal document between Organization and Employee.
"""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class Contract(SQLModel, table=True):
    """A legal document between the Organization and an Employee.

    Status: draft / pending_signature / active / expired / terminated / cancelled.
    One Employee may have multiple contracts.
    """

    __tablename__ = "contracts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(foreign_key="employees.id", nullable=False, index=True)
    contract_number: str | None = Field(default=None, max_length=50, unique=True)
    template_id: UUID | None = Field(default=None, foreign_key="contract_templates.id")
    contract_type: str = Field(max_length=30, nullable=False)
    status: str = Field(default="draft", max_length=30, nullable=False)
    signed_on: date | None = Field(default=None)
    started_on: date | None = Field(default=None)
    ended_on: date | None = Field(default=None)
    file_path: str | None = Field(default=None)
    content: str | None = Field(default=None)
    signed_document_path: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_by: UUID = Field(foreign_key="users.id", nullable=False)
    updated_by: UUID | None = Field(default=None, foreign_key="users.id")
