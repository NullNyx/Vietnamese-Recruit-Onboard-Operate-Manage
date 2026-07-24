"""Create assistant quality tables: chat_sessions, feedback_events, tool_call_events.

Stores per-session chat metadata, user feedback (thumbs up/down), and
tool call latency/outcome events for the AI Assistant quality dashboard.

Revision ID: 075
Revises: 074
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "075"
down_revision: str | None = "074"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create assistant_chat_sessions, assistant_feedback_events, assistant_tool_call_events."""
    # ------------------------------------------------------------------
    # assistant_chat_sessions — one row per frontend ChatInterface mount
    # ------------------------------------------------------------------
    op.create_table(
        "assistant_chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("assistant_type", sa.String(length=10), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=True, index=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # assistant_feedback_events — thumbs up/down on specific messages
    # ------------------------------------------------------------------
    op.create_table(
        "assistant_feedback_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("message_index", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=4), nullable=False),
        sa.Column("optional_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["assistant_chat_sessions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # assistant_tool_call_events — latency + outcome per tool invocation
    # ------------------------------------------------------------------
    op.create_table(
        "assistant_tool_call_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("arguments_hash", sa.String(length=64), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["assistant_chat_sessions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop assistant_tool_call_events, assistant_feedback_events, assistant_chat_sessions."""
    op.drop_table("assistant_tool_call_events")
    op.drop_table("assistant_feedback_events")
    op.drop_table("assistant_chat_sessions")
