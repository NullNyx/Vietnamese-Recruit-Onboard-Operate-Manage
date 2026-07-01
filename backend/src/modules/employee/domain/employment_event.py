"""EmploymentEvent domain entity.

Records changes in an Employee's data or status for audit trail.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


class EmploymentEvent(SQLModel, table=True):
    """A recorded change in an Employee's data or status.

    Event types: profile_update, promotion, transfer, status_change,
    termination, document_update, contract_update.
    Stores before/after snapshot and the HR actor who made the change.
    """

    __tablename__ = "employment_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(foreign_key="employees.id", nullable=False, index=True)
    event_type: str = Field(
        max_length=50,
        nullable=False,
        description="profile_update/promotion/transfer/status_change/termination/document_update/contract_update",
    )
    before_json: dict | None = Field(default=None, sa_column=Column(JSON))
    after_json: dict | None = Field(default=None, sa_column=Column(JSON))
    actor_hr_id: UUID = Field(foreign_key="users.id", nullable=False)
    note: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
