"""Support Job Application source splits and message linking.

Revision ID: 062
Revises: 061
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "062"
down_revision: str | None = "061"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_job_applications_gmail_message_id", table_name="job_applications")
    op.create_index(
        "ix_job_applications_gmail_message_id",
        "job_applications",
        ["gmail_message_id"],
        unique=False,
    )
    empty_json = sa.text("'[]'::jsonb")
    op.add_column(
        "job_applications",
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=empty_json,
        ),
    )
    op.add_column(
        "job_applications",
        sa.Column(
            "source_hints",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=empty_json,
        ),
    )
    op.add_column(
        "job_applications",
        sa.Column(
            "message_references",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=empty_json,
        ),
    )
    op.add_column(
        "job_applications",
        sa.Column(
            "audit_history",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=empty_json,
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE job_applications
            SET message_references = jsonb_build_array(
                jsonb_build_object(
                    'email_message_id', source_email_message_id::text,
                    'gmail_message_id', gmail_message_id,
                    'gmail_thread_id', gmail_thread_id,
                    'link_type', 'source'
                )
            )
            """
        )
    )

    op.create_table(
        "job_application_link_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recruitment_inbox_item_id", sa.Uuid(), nullable=False),
        sa.Column("target_job_application_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("proposed_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("resolved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["recruitment_inbox_item_id"],
            ["recruitment_inbox_items.id"],
            name="fk_link_proposals_inbox_item_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_job_application_id"],
            ["job_applications.id"],
            name="fk_link_proposals_target_application_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["proposed_by_user_id"],
            ["users.id"],
            name="fk_link_proposals_proposed_by_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_user_id"],
            ["users.id"],
            name="fk_link_proposals_resolved_by_user_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_link_proposals_inbox_item_id",
        "job_application_link_proposals",
        ["recruitment_inbox_item_id"],
    )
    op.create_index(
        "ix_link_proposals_target_application_id",
        "job_application_link_proposals",
        ["target_job_application_id"],
    )
    op.create_index(
        "ix_link_proposals_status",
        "job_application_link_proposals",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_link_proposals_status", table_name="job_application_link_proposals")
    op.drop_index(
        "ix_link_proposals_target_application_id",
        table_name="job_application_link_proposals",
    )
    op.drop_index(
        "ix_link_proposals_inbox_item_id",
        table_name="job_application_link_proposals",
    )
    op.drop_table("job_application_link_proposals")

    op.drop_column("job_applications", "audit_history")
    op.drop_column("job_applications", "message_references")
    op.drop_column("job_applications", "source_hints")
    op.drop_column("job_applications", "evidence")
    op.drop_index("ix_job_applications_gmail_message_id", table_name="job_applications")
    op.create_index(
        "ix_job_applications_gmail_message_id",
        "job_applications",
        ["gmail_message_id"],
        unique=True,
    )
