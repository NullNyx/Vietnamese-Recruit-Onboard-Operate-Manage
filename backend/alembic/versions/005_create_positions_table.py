"""Create positions table.

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:04.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the positions table with FK to departments."""
    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
    )

    # Unique index on position name
    op.create_index("ix_positions_name", "positions", ["name"], unique=True)


def downgrade() -> None:
    """Drop the positions table."""
    op.drop_index("ix_positions_name", table_name="positions")
    op.drop_table("positions")
