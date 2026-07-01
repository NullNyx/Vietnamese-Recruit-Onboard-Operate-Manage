"""Domain entities for the Employee Management module.

Defines the SQLModel table classes for Employee, Department, Position,
and EmployeeDocument that map to PostgreSQL tables used for HR personnel
management.
"""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class Department(SQLModel, table=True):
    """Represents an organizational unit (e.g., Engineering, HR, Sales).

    Departments group employees and serve as a reference for positions.
    Cannot be deleted if active employees are assigned to it.
    """

    __tablename__ = "departments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, nullable=False)
    description: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Position(SQLModel, table=True):
    """Represents a job title within a department (e.g., Senior Developer, Manager).

    Positions are optionally linked to a department. Cannot be deleted
    if active employees hold this position.
    """

    __tablename__ = "positions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, nullable=False)
    department_id: UUID | None = Field(default=None, foreign_key="departments.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Employee(SQLModel, table=True):
    """Represents an employed person managed in the HR system.

    Employees are created manually, via Excel import, or promoted from
    candidates. Each employee receives an auto-generated employee_code
    in NV-XXX format. Deletion is soft (is_active=false).
    """

    __tablename__ = "employees"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_code: str = Field(max_length=20, unique=True, nullable=False)
    full_name: str = Field(max_length=255, nullable=False)
    email: str | None = Field(default=None, max_length=255, unique=True, index=True)
    phone: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = Field(default=None)
    gender: str | None = Field(default=None, max_length=10)
    address: str | None = Field(default=None)
    department_id: UUID | None = Field(default=None, foreign_key="departments.id")
    position_id: UUID | None = Field(default=None, foreign_key="positions.id")
    manager_id: UUID | None = Field(default=None, foreign_key="employees.id")
    start_date: date | None = Field(default=None)
    id_number: str | None = Field(default=None, max_length=20)
    personal_tax_code: str | None = Field(default=None, max_length=20, alias="tax_code")
    contract_type: str | None = Field(default=None, max_length=20)
    employment_status: str = Field(default="active", max_length=20, nullable=False)
    termination_date: date | None = Field(default=None)
    candidate_id: UUID | None = Field(default=None)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    @property
    def tax_code(self) -> str | None:
        return self.personal_tax_code

    @tax_code.setter
    def tax_code(self, value: str | None) -> None:
        self.personal_tax_code = value


class EmployeeDocument(SQLModel, table=True):
    """Represents a document stored in the employee document vault.

    Documents are stored in MinIO at path employees/{employee_id}/{document_type}/{filename}.
    The vault is append-only — uploading a new version keeps previous versions.
    Documents are retained even when an employee is soft-deleted.
    """

    __tablename__ = "employee_documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(foreign_key="employees.id", nullable=False, index=True)
    document_type: str = Field(max_length=50, nullable=False)
    status: str = Field(default="uploaded", max_length=20, nullable=False)
    file_name: str = Field(max_length=255, nullable=False)
    storage_path: str = Field(nullable=False)
    file_size: int = Field(nullable=False)
    mime_type: str = Field(max_length=100, nullable=False)
    description: str | None = Field(default=None)
    uploaded_by_hr_id: UUID = Field(foreign_key="users.id", nullable=False)
    verified_by_hr_id: UUID | None = Field(default=None, foreign_key="users.id")
    verified_at: datetime | None = Field(default=None)
    expired_at: date | None = Field(default=None)
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

