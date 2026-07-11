"""Create interviews and interview_participants tables.

Revision ID: 046
Revises: 045
Create Date: 2026-07-11 00:00:00.000000+00:00
"""

import uuid
from datetime import datetime, timedelta, UTC
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "046"
down_revision: Union[str, None] = "045"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create interviews table
    op.create_table(
        "interviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="scheduled"),
        sa.Column("round_name", sa.String(length=255), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("calendar_event_id", sa.String(length=1024), nullable=True),
        sa.Column("needs_relink", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
    )
    op.create_index("ix_interviews_candidate_id", "interviews", ["candidate_id"])
    op.create_index("ix_interviews_calendar_event_id", "interviews", ["calendar_event_id"])

    # 2. Create interview_participants table
    op.create_table(
        "interview_participants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("employee_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
    )
    op.create_index("ix_interview_participants_interview_id", "interview_participants", ["interview_id"])

    # 3. Backfill existing candidates with calendar data
    bind = op.get_bind()
    candidates = bind.execute(
        sa.text(
            "SELECT id, calendar_event_id, interview_start_at, interview_timezone, name, email "
            "FROM candidates WHERE calendar_event_id IS NOT NULL OR interview_start_at IS NOT NULL"
        )
    ).fetchall()

    for cand in candidates:
        cand_id, event_id, start_at, timezone, name, email = cand
        if not start_at:
            start_at = datetime.now(UTC)
        if not timezone:
            timezone = "Asia/Ho_Chi_Minh"
        
        interview_id = uuid.uuid4()
        end_at = start_at + timedelta(hours=1)
        
        bind.execute(
            sa.text(
                "INSERT INTO interviews (id, candidate_id, status, round_name, start_at, end_at, timezone, calendar_event_id, needs_relink) "
                "VALUES (:id, :candidate_id, :status, :round_name, :start_at, :end_at, :timezone, :calendar_event_id, :needs_relink)"
            ),
            {
                "id": interview_id,
                "candidate_id": cand_id,
                "status": "scheduled",
                "round_name": "Legacy Interview",
                "start_at": start_at,
                "end_at": end_at,
                "timezone": timezone,
                "calendar_event_id": event_id,
                "needs_relink": False,
            }
        )
        
        bind.execute(
            sa.text(
                "INSERT INTO interview_participants (id, interview_id, type, email, name, employee_id) "
                "VALUES (:id, :interview_id, :type, :email, :name, :employee_id)"
            ),
            {
                "id": uuid.uuid4(),
                "interview_id": interview_id,
                "type": "candidate",
                "email": email or "",
                "name": name,
                "employee_id": None,
            }
        )


def downgrade() -> None:
    op.drop_table("interview_participants")
    op.drop_table("interviews")
