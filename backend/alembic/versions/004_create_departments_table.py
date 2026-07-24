"""Create departments table.

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:03.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the departments table."""
    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Unique index on department name
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)


def downgrade() -> None:
    """Drop the departments table."""
    op.drop_index("ix_departments_name", table_name="departments")
    op.drop_table("departments")
