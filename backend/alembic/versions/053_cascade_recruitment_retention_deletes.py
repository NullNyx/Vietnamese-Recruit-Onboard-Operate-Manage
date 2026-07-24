"""Cascade retention deletion through interview history.

Revision ID: 053
Revises: 052
"""

from alembic import op

revision = "053"
down_revision = "052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL cannot delete a Candidate while its historical interviews,
    # participants, or conflict snapshots still reference it. Retention only
    # reaches this point after the scheduled-interview guard in retention_job.
    op.drop_constraint("interviews_candidate_id_fkey", "interviews", type_="foreignkey")
    op.create_foreign_key(
        "interviews_candidate_id_fkey",
        "interviews",
        "candidates",
        ["candidate_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "interview_participants_interview_id_fkey", "interview_participants", type_="foreignkey"
    )
    op.create_foreign_key(
        "interview_participants_interview_id_fkey",
        "interview_participants",
        "interviews",
        ["interview_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "calendar_conflicts_candidate_id_fkey", "calendar_conflicts", type_="foreignkey"
    )
    op.create_foreign_key(
        "calendar_conflicts_candidate_id_fkey",
        "calendar_conflicts",
        "candidates",
        ["candidate_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "calendar_conflicts_candidate_id_fkey", "calendar_conflicts", type_="foreignkey"
    )
    op.create_foreign_key(
        "calendar_conflicts_candidate_id_fkey",
        "calendar_conflicts",
        "candidates",
        ["candidate_id"],
        ["id"],
    )
    op.drop_constraint(
        "interview_participants_interview_id_fkey", "interview_participants", type_="foreignkey"
    )
    op.create_foreign_key(
        "interview_participants_interview_id_fkey",
        "interview_participants",
        "interviews",
        ["interview_id"],
        ["id"],
    )
    op.drop_constraint("interviews_candidate_id_fkey", "interviews", type_="foreignkey")
    op.create_foreign_key(
        "interviews_candidate_id_fkey", "interviews", "candidates", ["candidate_id"], ["id"]
    )
