"""Create onboarding tables.

Adds the three tables owned by the onboarding module:

* ``onboarding_processes`` — one process per accepted Candidate. The
  ``candidate_id`` column carries a unique index, making "exactly one process
  per candidate" a database invariant (the backbone of idempotent event
  consumption).
* ``onboarding_tasks`` — the fixed four-item checklist for each process.
* ``onboarding_audit_logs`` — append-only audit trail for both system-driven
  (event consumption) and HR-driven (task completion, activation) changes.

The ``employees`` table is reused unchanged — ``candidate_id`` and ``is_active``
already exist (see revision 006), so no employee schema change is required here.

Revision ID: 028
Revises: 027
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "028"
down_revision: str | None = "027"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create onboarding_processes, onboarding_tasks, onboarding_audit_logs."""

    # --- onboarding_processes ---
    op.create_table(
        "onboarding_processes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="in_progress",
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
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
    )

    # Unique index on candidate_id: enforces the "exactly one process per
    # candidate" invariant (unique constraint) and serves the idempotency
    # lookup (index). This is the backbone of safe event re-delivery.
    op.create_index(
        "ix_onboarding_processes_candidate_id",
        "onboarding_processes",
        ["candidate_id"],
        unique=True,
    )
    op.create_index("ix_onboarding_processes_employee_id", "onboarding_processes", ["employee_id"])
    op.create_index("ix_onboarding_processes_status", "onboarding_processes", ["status"])

    # --- onboarding_tasks ---
    op.create_table(
        "onboarding_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("task_key", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=10),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["process_id"], ["onboarding_processes.id"]),
        sa.ForeignKeyConstraint(["completed_by_user_id"], ["users.id"]),
    )

    op.create_index("ix_onboarding_tasks_process_id", "onboarding_tasks", ["process_id"])

    # --- onboarding_audit_logs ---
    # Append-only: the application exposes only an append operation. UPDATE and
    # DELETE on this table are NOT permitted by the application — entries are an
    # immutable record of onboarding state changes (R8.4).
    op.create_table(
        "onboarding_audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("operation_type", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("candidate_id", sa.Uuid(), nullable=True),
        sa.Column("event_id", sa.String(length=255), nullable=True),
        sa.Column("previous_value", JSONB(), nullable=True),
        sa.Column("new_value", JSONB(), nullable=True),
        sa.Column("change_summary", sa.String(length=500), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        comment=(
            "Append-only audit trail for the onboarding module. "
            "UPDATE/DELETE are not permitted by the application; entries are "
            "an immutable record of onboarding state changes."
        ),
    )

    op.create_index("ix_onboarding_audit_logs_user_id", "onboarding_audit_logs", ["user_id"])
    op.create_index(
        "ix_onboarding_audit_logs_operation_type", "onboarding_audit_logs", ["operation_type"]
    )
    op.create_index("ix_onboarding_audit_logs_entity_id", "onboarding_audit_logs", ["entity_id"])
    op.create_index(
        "ix_onboarding_audit_logs_candidate_id", "onboarding_audit_logs", ["candidate_id"]
    )
    op.create_index("ix_onboarding_audit_logs_created_at", "onboarding_audit_logs", ["created_at"])


def downgrade() -> None:
    """Drop the three onboarding tables in reverse dependency order."""
    op.drop_index("ix_onboarding_audit_logs_created_at", table_name="onboarding_audit_logs")
    op.drop_index("ix_onboarding_audit_logs_candidate_id", table_name="onboarding_audit_logs")
    op.drop_index("ix_onboarding_audit_logs_entity_id", table_name="onboarding_audit_logs")
    op.drop_index("ix_onboarding_audit_logs_operation_type", table_name="onboarding_audit_logs")
    op.drop_index("ix_onboarding_audit_logs_user_id", table_name="onboarding_audit_logs")
    op.drop_table("onboarding_audit_logs")

    op.drop_index("ix_onboarding_tasks_process_id", table_name="onboarding_tasks")
    op.drop_table("onboarding_tasks")

    op.drop_index("ix_onboarding_processes_status", table_name="onboarding_processes")
    op.drop_index("ix_onboarding_processes_employee_id", table_name="onboarding_processes")
    op.drop_index("ix_onboarding_processes_candidate_id", table_name="onboarding_processes")
    op.drop_table("onboarding_processes")
