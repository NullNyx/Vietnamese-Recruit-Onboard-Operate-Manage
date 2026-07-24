"""Add local auth fields to users.

Revision ID: 043
Revises: 042
Create Date: 2026-07-10 00:00:00.000000+07:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "043"
down_revision: str | None = "042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("employee_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("users", "google_sub", existing_type=sa.String(length=255), nullable=True)
    op.create_unique_constraint(
        "uq_users_employee_id",
        "users",
        ["employee_id"],
    )
    op.create_foreign_key(
        "fk_users_employee_id_employees",
        "users",
        "employees",
        ["employee_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_employee_id_employees", "users", type_="foreignkey")
    op.drop_constraint("uq_users_employee_id", "users", type_="unique")
    op.alter_column("users", "google_sub", existing_type=sa.String(length=255), nullable=False)
    op.drop_column("users", "must_change_password")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "employee_id")
