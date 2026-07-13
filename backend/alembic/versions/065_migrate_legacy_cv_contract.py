"""Migrate unresolved legacy ``cv`` classifications to Job Applications.

Revision ID: 065
Revises: 064
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "065"
down_revision: str | None = "064"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill only legacy CV emails that never produced a Candidate.

    The statement is intentionally idempotent: an existing Job Application for
    either the source email or Gmail message prevents another insert. Candidate
    history is used only as an exclusion and is never updated.
    """
    op.execute(
        sa.text(
            """
            WITH eligible AS (
                SELECT email.*
                FROM email_messages AS email
                WHERE email.category = 'cv'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM candidates AS candidate
                      WHERE candidate.source_email_message_id = email.id
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM job_applications AS application
                      WHERE application.source_email_message_id = email.id
                         OR application.gmail_message_id = email.gmail_message_id
                  )
            ),
            inserted AS (
                INSERT INTO job_applications (
                    id,
                    source_email_message_id,
                    gmail_message_id,
                    gmail_thread_id,
                    source,
                    applicant_name,
                    applicant_email,
                    sender_name,
                    sender_email,
                    evidence,
                    source_hints,
                    message_references,
                    audit_history,
                    status
                )
                SELECT
                    gen_random_uuid(),
                    email.id,
                    email.gmail_message_id,
                    email.gmail_thread_id,
                    'direct',
                    NULLIF(email.sender_name, ''),
                    NULLIF(email.sender_email, ''),
                    email.sender_name,
                    email.sender_email,
                    '[]'::jsonb,
                    '[]'::jsonb,
                    jsonb_build_array(
                        jsonb_build_object(
                            'email_message_id', email.id::text,
                            'gmail_message_id', email.gmail_message_id,
                            'gmail_thread_id', email.gmail_thread_id,
                            'link_type', 'source'
                        )
                    ),
                    jsonb_build_array(
                        jsonb_build_object(
                            'action', 'legacy_classification_migrated',
                            'legacy_intent', 'cv',
                            'occurred_at', CURRENT_TIMESTAMP
                        )
                    ),
                    'new'
                FROM eligible AS email
                RETURNING source_email_message_id
            )
            UPDATE email_messages AS email
            SET category = 'job_application',
                updated_at = CURRENT_TIMESTAMP
            FROM inserted
            WHERE email.id = inserted.source_email_message_id
            """
        )
    )


def downgrade() -> None:
    """Preserve migrated Job Applications and their audit history."""
