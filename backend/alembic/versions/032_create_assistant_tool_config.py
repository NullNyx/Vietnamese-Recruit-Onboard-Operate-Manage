"""Create assistant_tool_config table.

Stores per-tool enable/disable toggles for the AI Assistant.
Admin manages tools via /api/admin/assistant-tools; the ToolRegistry
reads this table at chat time to filter which tools the LLM sees.

Revision ID: 031
Revises: 030
Create Date: 2026-06-04
"""

import sqlalchemy as sa

from alembic import op

revision: str = "032"
down_revision: str | None = "031"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create assistant_tool_config with tool_name PK."""
    op.create_table(
        "assistant_tool_config",
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("tool_name"),
    )


def downgrade() -> None:
    """Drop assistant_tool_config."""
    op.drop_table("assistant_tool_config")
