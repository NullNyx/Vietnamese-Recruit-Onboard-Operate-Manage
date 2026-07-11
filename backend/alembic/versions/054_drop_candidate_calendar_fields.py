"""Drop legacy candidate calendar fields after verifying Interview coverage.

Safely removes the three legacy calendar columns from the ``candidates``
table that were added in ``029_add_interview_calendar_fields.py``. Every
non-null value in those columns MUST have a corresponding ``interviews``
row; if any orphan values are found the migration aborts with a detailed
verification report so the operator can intervene before the columns are
dropped.

Upgrade
-------
1.  Verify that every ``candidates`` row with a non-null
    ``calendar_event_id`` has at least one ``interviews`` row with the
    matching ``calendar_event_id``.
2.  Drop the partial unique index ``ix_candidates_calendar_event_id``.
3.  Drop the three columns ``calendar_event_id``,
    ``interview_start_at``, and ``interview_timezone``.

Downgrade
---------
Recreates the columns and the partial unique index but documents that
*no automatic data restore is performed* — the operator must repopulate
the columns from the ``interviews`` table (or accept NULLs for newly
scheduled interviews, which use the ``interviews`` table exclusively).

Revision ID: 054
Revises: 053
"""

import sqlalchemy as sa

from alembic import op

revision: str = "054"
down_revision: str | None = "053"
branch_labels: str | None = None
depends_on: str | None = None


def _detect_backend() -> str:
    """Return the backend dialect name (e.g. ``postgresql``)."""
    ctx = op.get_context()
    return ctx.dialect.name


def upgrade() -> None:
    """Verify every non-null legacy calendar field and drop the columns."""

    # ------------------------------------------------------------------
    # Step 1 — verify every non-null calendar_event_id has a matching
    #           Interview row before we remove the legacy columns.
    # ------------------------------------------------------------------
    bind = op.get_bind()
    # Verify all legacy calendar-bearing candidates, including rows whose
    # event id was missing but whose time/timezone was populated.
    incomplete = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM candidates "
            "WHERE (interview_start_at IS NOT NULL OR interview_timezone IS NOT NULL) "
            "AND NOT EXISTS (SELECT 1 FROM interviews i WHERE i.candidate_id = candidates.id)"
        )
    ).scalar_one()
    if incomplete:
        raise AssertionError(
            f"MIGRATION VERIFICATION FAILED: {incomplete} candidate(s) have "
            "legacy calendar time/timezone without an Interview row"
        )
    rows = bind.execute(
        sa.text(
            "SELECT id, calendar_event_id, name, email "
            "FROM candidates "
            "WHERE calendar_event_id IS NOT NULL "
            "ORDER BY created_at DESC"
        )
    ).fetchall()

    orphans: list[dict[str, str]] = []
    for row in rows:
        c_id, cal_event_id, name, email = row
        match = bind.execute(
            sa.text(
                "SELECT 1 FROM interviews "
                "WHERE candidate_id = :cid AND calendar_event_id = :eid "
                "LIMIT 1"
            ),
            {"cid": c_id, "eid": cal_event_id},
        ).fetchone()
        if match is None:
            orphans.append(
                {
                    "candidate_id": str(c_id),
                    "calendar_event_id": str(cal_event_id),
                    "name": name,
                    "email": email,
                }
            )

    if orphans:
        report_lines = [
            "────────── MIGRATION VERIFICATION FAILED ──────────",
            "",
            f"Found {len(orphans)} candidate(s) with legacy calendar_event_id",
            "that have no matching Interview record:",
            "",
        ]
        for o in orphans:
            report_lines.append(
                f"  · Candidate {o['candidate_id']} "
                f"({o['name']} <{o['email']}>)"
                f"\n    calendar_event_id = {o['calendar_event_id']}"
            )
        report_lines.extend(
            [
                "",
                "Action required:",
                "  Before this migration can proceed, ensure every legacy",
                "  calendar_event_id has a corresponding Interview row.",
                "  You can create them manually or accept NULL (set to NULL",
                "  on the candidate first, then re-run the migration).",
                "",
                "──────────────────────────────────────────────────",
            ]
        )
        raise AssertionError("\n".join(report_lines))

    # ------------------------------------------------------------------
    # Step 2 — drop the partial unique index
    # ------------------------------------------------------------------
    op.drop_index("ix_candidates_calendar_event_id", table_name="candidates")

    # ------------------------------------------------------------------
    # Step 3 — drop the legacy columns
    # ------------------------------------------------------------------
    op.drop_column("candidates", "calendar_event_id")
    op.drop_column("candidates", "interview_start_at")
    op.drop_column("candidates", "interview_timezone")


def downgrade() -> None:
    """Recreate columns and index; no automatic data restore.

    .. important::

       This downgrade recreates the columns and index but does **not**
       back-fill any data. Rows that had non-null values before the
       upgrade will now have ``NULL`` in all three columns. To repopulate
       them, run a query such as::

           UPDATE candidates c
           SET
               calendar_event_id  = i.calendar_event_id,
               interview_start_at = i.start_at,
               interview_timezone = i.timezone
           FROM interviews i
           WHERE i.candidate_id = c.id
             AND i.status = 'scheduled'
             AND c.calendar_event_id IS NULL;

       Or accept ``NULL`` — newly scheduled interviews in the legacy
       pipeline exclusively use the ``interviews`` table.
    """

    op.add_column(
        "candidates",
        sa.Column("calendar_event_id", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column("interview_start_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column("interview_timezone", sa.String(length=64), nullable=True),
    )

    op.create_index(
        "ix_candidates_calendar_event_id",
        "candidates",
        ["calendar_event_id"],
        unique=True,
        postgresql_where=sa.text("calendar_event_id IS NOT NULL"),
    )
