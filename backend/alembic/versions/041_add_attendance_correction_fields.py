"""Add missing correction fields to attendance_records.

Revision ID: 041
Revises: 040
Create Date: 2026-06-13 22:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("attendance_records")]

    if "corrected_by_user_id" not in columns:
        op.add_column(
            "attendance_records", sa.Column("corrected_by_user_id", sa.Uuid(), nullable=True)
        )
    if "corrected_at" not in columns:
        op.add_column(
            "attendance_records",
            sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "correction_reason" not in columns:
        op.add_column(
            "attendance_records", sa.Column("correction_reason", sa.Text(), nullable=True)
        )
    if "previous_check_in_at" not in columns:
        op.add_column(
            "attendance_records",
            sa.Column("previous_check_in_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "previous_check_out_at" not in columns:
        op.add_column(
            "attendance_records",
            sa.Column("previous_check_out_at", sa.DateTime(timezone=True), nullable=True),
        )

    fks = inspector.get_foreign_keys("attendance_records")
    fk_names = [fk["name"] for fk in fks]
    if "fk_attendance_records_corrected_by_user_id" not in fk_names:
        op.create_foreign_key(
            "fk_attendance_records_corrected_by_user_id",
            "attendance_records",
            "users",
            ["corrected_by_user_id"],
            ["id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    fks = inspector.get_foreign_keys("attendance_records")
    fk_names = [fk["name"] for fk in fks]
    if "fk_attendance_records_corrected_by_user_id" in fk_names:
        op.drop_constraint(
            "fk_attendance_records_corrected_by_user_id", "attendance_records", type_="foreignkey"
        )

    columns = [c["name"] for c in inspector.get_columns("attendance_records")]
    if "previous_check_out_at" in columns:
        op.drop_column("attendance_records", "previous_check_out_at")
    if "previous_check_in_at" in columns:
        op.drop_column("attendance_records", "previous_check_in_at")
    if "correction_reason" in columns:
        op.drop_column("attendance_records", "correction_reason")
    if "corrected_at" in columns:
        op.drop_column("attendance_records", "corrected_at")
    if "corrected_by_user_id" in columns:
        op.drop_column("attendance_records", "corrected_by_user_id")
