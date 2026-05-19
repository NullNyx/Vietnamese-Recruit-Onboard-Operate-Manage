"""Create employees table.

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:05.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the employees table with FKs to departments and positions."""
    op.create_table(
        "employees",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employee_code", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=10), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column("position_id", sa.Uuid(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("id_number", sa.String(length=20), nullable=True),
        sa.Column("tax_code", sa.String(length=20), nullable=True),
        sa.Column("contract_type", sa.String(length=20), nullable=True),
        sa.Column("candidate_id", sa.Uuid(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"]),
    )

    # Unique indexes
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"], unique=True)

    # Non-unique indexes for FK lookups
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_position_id", "employees", ["position_id"])


def downgrade() -> None:
    """Drop the employees table."""
    op.drop_index("ix_employees_position_id", table_name="employees")
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_index("ix_employees_employee_code", table_name="employees")
    op.drop_index("ix_employees_email", table_name="employees")
    op.drop_table("employees")
