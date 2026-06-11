"""Add leave-specific columns to employee_requests.

Adds leave_type, start_date, end_date for leave request support.
Updates the request_type check constraint if any.

Revision ID: 035
Revises: 034
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "036"
down_revision: str | None = "034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add leave-specific columns to employee_requests."""
    op.add_column("employee_requests", sa.Column("leave_type", sa.Text(), nullable=True))
    op.add_column("employee_requests", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("employee_requests", sa.Column("end_date", sa.Date(), nullable=True))
    op.create_index("ix_employee_requests_start_date", "employee_requests", ["start_date"])


def downgrade() -> None:
    """Remove leave-specific columns."""
    op.drop_index("ix_employee_requests_start_date", table_name="employee_requests")
    op.drop_column("employee_requests", "end_date")
    op.drop_column("employee_requests", "start_date")
    op.drop_column("employee_requests", "leave_type")
