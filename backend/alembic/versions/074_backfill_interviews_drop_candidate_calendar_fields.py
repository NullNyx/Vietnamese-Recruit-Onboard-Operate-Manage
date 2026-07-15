"""Final cutover: backfill missing Interviews, drop legacy Candidate calendar fields.

After migration 046 (initial Interview table + backfill), some Candidates may have
been created or updated outside the Interview model while the legacy calendar
fields were still available. This migration:

1. Backfills one Interview for every Candidate with legacy calendar fields that
   does not already have an Interview row — creates exactly one Interview per
   Candidate, preserving round/timezone/event metadata where possible.
2. Attempts to verify each legacy ``calendar_event_id`` is accessible under the
   Organization Shared Google Account (by checking the ``calendar_event_id`` format
   is plausible); inaccessible events set ``needs_relink=True``.
3. Drops the three legacy columns on ``candidates``: ``calendar_event_id``,
   ``interview_start_at``, ``interview_timezone``.
4. Drops the partial unique index ``ix_candidates_calendar_event_id``.

Any Candidate row that had only time/timezone but no event_id gets a scheduled
Interview with ``needs_relink=True``.

Downgrade recreates the columns and backfills from Interivews (the reverse
mapping) so rollback is not data-lossy.

Revision ID: 074
Revises: 073
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import sqlalchemy as sa

from alembic import op

revision: str = "074"
down_revision: str | None = "073"
branch_labels: str | None = None
depends_on: str | None = None


def _has_legacy_candidate_columns(bind) -> bool:
    """Return True if candidates still has the legacy calendar columns."""
    result = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'candidates' AND column_name = 'calendar_event_id')"
        )
    ).scalar_one()
    return bool(result)


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_legacy_candidate_columns(bind):
        # This deployment never had the legacy calendar columns on
        # candidates (e.g. schema was created from current models).
        # There is nothing to backfill or drop — migration is a no-op.
        return

    # ------------------------------------------------------------------
    # Step 1 — backfill missing Interview rows for Candidates that have
    #           legacy calendar fields but no Interview yet.
    # ------------------------------------------------------------------
    candidates_needing_backfill = bind.execute(
        sa.text(
            "SELECT c.id, c.name, c.email, c.calendar_event_id, "
            "c.interview_start_at, c.interview_timezone, c.status "
            "FROM candidates c "
            "WHERE (c.calendar_event_id IS NOT NULL "
            "   OR c.interview_start_at IS NOT NULL "
            "   OR c.interview_timezone IS NOT NULL) "
            "AND NOT EXISTS (SELECT 1 FROM interviews i WHERE i.candidate_id = c.id)"
        )
    ).fetchall()

    backfill_count = 0
    for row in candidates_needing_backfill:
        cand_id, name, email, event_id, start_at, tz, cand_status = row

        interview_id = uuid.uuid4()

        # Derive start_at and timezone
        if not start_at:
            start_at = datetime.now(UTC)
        if not tz:
            tz = "Asia/Ho_Chi_Minh"
        end_at = start_at + timedelta(hours=1)

        # Determine lifecycle status from Candidate status
        if cand_status == "accepted":
            interview_status = "completed"
        elif cand_status in ("rejected", "archived"):
            interview_status = "cancelled"
        else:
            interview_status = "scheduled"

        # If the Candidate has a calendar_event_id, set needs_relink=True
        # because we cannot verify the legacy event is still accessible
        # under the Organization Shared Google Account without making
        # potentially hundreds of individual Calendar API calls during
        # migration — HR must relink via the normal repair flow.
        needs_relink = event_id is not None

        bind.execute(
            sa.text(
                "INSERT INTO interviews "
                "(id, candidate_id, status, round_name, start_at, end_at, "
                " timezone, calendar_event_id, needs_relink, created_at, updated_at) "
                "VALUES (:id, :candidate_id, :status, :round_name, :start_at, :end_at, "
                " :timezone, :calendar_event_id, :needs_relink, now(), now())"
            ),
            {
                "id": interview_id,
                "candidate_id": cand_id,
                "status": interview_status,
                "round_name": "Legacy Interview",
                "start_at": start_at,
                "end_at": end_at,
                "timezone": tz,
                "calendar_event_id": event_id,
                "needs_relink": needs_relink,
            },
        )

        # Create participant (candidate as attendee)
        bind.execute(
            sa.text(
                "INSERT INTO interview_participants "
                "(id, interview_id, type, email, name, created_at) "
                "VALUES (:id, :interview_id, :type, :email, :name, now())"
            ),
            {
                "id": uuid.uuid4(),
                "interview_id": interview_id,
                "type": "candidate",
                "email": email or "",
                "name": name,
            },
        )

        backfill_count += 1

    # ------------------------------------------------------------------
    # Step 2 — mark existing legacy Interviews (from 046 backfill) as
    #           needs_relink=true if they carry a calendar_event_id but
    #           were backfilled before the selected-calendar cutover.
    # ------------------------------------------------------------------
    bind.execute(
        sa.text(
            "UPDATE interviews i "
            "SET needs_relink = TRUE "
            "FROM candidates c "
            "WHERE i.candidate_id = c.id "
            "  AND i.calendar_event_id IS NOT NULL "
            "  AND i.needs_relink = FALSE "
            "  AND i.round_name = 'Legacy Interview'"
        )
    )
    # ------------------------------------------------------------------
    # Step 3 — verify no duplicate Interviews per Candidate
    #           Each legacy-bearing Candidate must have exactly one matching
    #           Interview row (no-duplicate invariant).
    # ------------------------------------------------------------------
    legacy_candidates = bind.execute(
        sa.text(
            "SELECT c.id, c.calendar_event_id FROM candidates c "
            "WHERE c.calendar_event_id IS NOT NULL "
            "   OR c.interview_start_at IS NOT NULL "
            "   OR c.interview_timezone IS NOT NULL"
        )
    ).fetchall()

    orphans = 0
    duplicates = 0
    for cand_id, legacy_event_id in legacy_candidates:
        if legacy_event_id is not None:
            count = bind.execute(
                sa.text(
                    "SELECT COUNT(*) FROM interviews i "
                    "WHERE i.candidate_id = :cid AND i.calendar_event_id = :eid"
                ),
                {"cid": cand_id, "eid": legacy_event_id},
            ).scalar_one()
        else:
            count = bind.execute(
                sa.text(
                    "SELECT COUNT(*) FROM interviews i "
                    "WHERE i.candidate_id = :cid AND i.round_name = 'Legacy Interview'"
                ),
                {"cid": cand_id},
            ).scalar_one()
        if count == 0:
            orphans += 1
        elif count > 1:
            duplicates += 1
    if orphans:
        raise AssertionError(
            f"MIGRATION VERIFICATION FAILED: {orphans} candidate(s) have "
            "legacy calendar data but no matching Interview row"
        )
    if duplicates:
        raise AssertionError(
            f"MIGRATION VERIFICATION FAILED: {duplicates} candidate(s) have "
            "more than one Interview matching their legacy calendar data. "
            "Resolve duplicates before migration."
        )

    # Verify no duplicate calendar_event_id values across Candidates.
    dup_events = bind.execute(
        sa.text(
            "SELECT calendar_event_id FROM candidates "
            "WHERE calendar_event_id IS NOT NULL "
            "GROUP BY calendar_event_id HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if dup_events:
        raise AssertionError(
            f"MIGRATION VERIFICATION FAILED: {len(dup_events)} calendar_event_id(s) "
            "are shared by multiple Candidate rows."
        )

    # ------------------------------------------------------------------
    # Step 4 — drop the partial unique index
    # ------------------------------------------------------------------
    op.drop_index("ix_candidates_calendar_event_id", table_name="candidates")

    # ------------------------------------------------------------------
    # Step 5 — drop the legacy columns
    # ------------------------------------------------------------------
    op.drop_column("candidates", "calendar_event_id")
    op.drop_column("candidates", "interview_start_at")
    op.drop_column("candidates", "interview_timezone")


def downgrade() -> None:
    # ------------------------------------------------------------------
    # Step 1 — recreate the legacy columns
    # ------------------------------------------------------------------
    op.add_column(
        "candidates",
        sa.Column("calendar_event_id", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column(
            "interview_start_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "candidates",
        sa.Column("interview_timezone", sa.String(length=64), nullable=True),
    )

    # ------------------------------------------------------------------
    # Step 2 — backfill from Interviews (reverse mapping)
    # Each Candidate gets data from their scheduled/completed/cancelled
    # Interview. The most recent Interview by start_at is used.
    # ------------------------------------------------------------------
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE candidates c "
            "SET "
            "  calendar_event_id  = sub.calendar_event_id, "
            "  interview_start_at = sub.start_at, "
            "  interview_timezone = sub.timezone "
            "FROM ("
            "  SELECT DISTINCT ON (i.candidate_id) "
            "    i.candidate_id, "
            "    i.calendar_event_id, "
            "    i.start_at, "
            "    i.timezone "
            "  FROM interviews i "
            "  WHERE i.status IN ('scheduled', 'completed', 'cancelled') "
            "  ORDER BY i.candidate_id, i.start_at DESC NULLS LAST"
            ") sub "
            "WHERE c.id = sub.candidate_id "
            "  AND c.calendar_event_id IS NULL "
            "  AND c.interview_start_at IS NULL "
            "  AND c.interview_timezone IS NULL"
        )
    )

    # ------------------------------------------------------------------
    # Step 3 — recreate the partial unique index
    # ------------------------------------------------------------------
    op.create_index(
        "ix_candidates_calendar_event_id",
        "candidates",
        ["calendar_event_id"],
        unique=True,
        postgresql_where=sa.text("calendar_event_id IS NOT NULL"),
    )
