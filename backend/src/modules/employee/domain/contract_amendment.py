"""ContractAmendment domain entity.

Supplementary document attached to an active Contract.
"""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class ContractAmendment(SQLModel, table=True):
    """A supplementary document attached to an active Contract.

    Status: draft / pending_signature / signed / cancelled.
    """

    __tablename__ = "contract_amendments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    contract_id: UUID = Field(foreign_key="contracts.id", nullable=False, index=True)
    name: str = Field(max_length=255, nullable=False)
    content: str = Field(nullable=False)
    file_path: str | None = Field(default=None)
    signed_document_path: str | None = Field(default=None)
    status: str = Field(default="draft", max_length=30, nullable=False)
    signed_on: date | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_by: UUID = Field(foreign_key="users.id", nullable=False)
