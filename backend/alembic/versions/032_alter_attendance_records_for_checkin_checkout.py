"""Recreate attendance_records table for check-in/check-out from office network.

Migration 027 dropped attendance_records table. This migration recreates it
with the new schema for employee-owned check-in/check-out per ADR-0010.

Revision ID: 032
Revises: 031
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "032"
down_revision: str | Sequence[str] | None = "031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create attendance_records table for office network check-in/out."""
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_in_ip", sa.String(length=45), nullable=True),
        sa.Column("check_out_ip", sa.String(length=45), nullable=True),
        sa.Column("check_in_user_agent", sa.String(length=512), nullable=True),
        sa.Column("check_out_user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "source", sa.String(length=20), nullable=False, server_default="web"
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
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.UniqueConstraint(
            "employee_id", "work_date", name="uq_attendance_employee_date"
        ),
    )

    op.create_index(
        "ix_attendance_records_employee_id",
        "attendance_records",
        ["employee_id"],
    )
    op.create_index(
        "ix_attendance_records_work_date",
        "attendance_records",
        ["work_date"],
    )


def downgrade() -> None:
    """Drop attendance_records table."""
    op.drop_index(
        "ix_attendance_records_work_date", table_name="attendance_records"
    )
    op.drop_index(
        "ix_attendance_records_employee_id", table_name="attendance_records"
    )
    op.drop_table("attendance_records")
