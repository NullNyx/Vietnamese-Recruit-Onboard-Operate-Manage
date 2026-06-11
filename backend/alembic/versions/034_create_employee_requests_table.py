"""Create employee_requests table.

Stores Employee Request lifecycle fields with overtime-specific columns.
Leave-specific columns will be added when leave requests are implemented.

Revision ID: 034
Revises: 033
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "034"
down_revision: str | None = "033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the employee_requests table."""
    op.create_table(
        "employee_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("request_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'submitted'")),
        # Timestamps
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        # Cancellation
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        # Overtime-specific fields
        sa.Column("work_date", sa.Date(), nullable=True, index=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("project_or_task", sa.String(255), nullable=True),
        # Audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop employee_requests table."""
    op.drop_table("employee_requests")
