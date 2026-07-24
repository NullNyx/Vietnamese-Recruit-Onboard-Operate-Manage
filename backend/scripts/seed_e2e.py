"""E2E seed script — reset DB to clean state for Playwright tests.

Truncates core tables (users, organization_settings, candidates, employees)
with CASCADE so all dependent rows are cleaned.  Optionally inserts a minimal
admin user and organization_settings row (``--setup-complete``) for tests that
need a pre-configured deployment without running the First-Run Setup wizard.

When ``--setup-complete`` is passed, the script also seeds comprehensive E2E
test data: an employee + employee account, job openings, candidates in various
statuses, an interview, a published payslip, and a whitelist entry.

Usage::

    cd backend
    python scripts/seed_e2e.py                    # setup_complete=false (default)
    python scripts/seed_e2e.py --setup-complete    # setup_complete=true
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text

# Load backend/.env so AuthSettings can find AUTH_* vars
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


# ---------------------------------------------------------------------------
# Tables to truncate (in dependency-safe order — CASCADE handles the rest)
# ---------------------------------------------------------------------------
CORE_TABLES = [
    "users",
    "organization_settings",
    "candidates",
    "employees",
    "job_openings",
    "interviews",
    "payslips",
    "whitelist_entries",
    "outbound_emails",
    ]


def _get_db_url() -> str:
    """Return the sync (psycopg2) database URL from AuthSettings."""
    from src.modules.identity.infrastructure.config import AuthSettings

    settings = AuthSettings()  # type: ignore[call-arg]
    url = settings.database_url
    # Remove async driver so we can use sync psycopg2
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("+asyncpg", "", 1)
    return url


def _make_session():
    from sqlalchemy import create_engine
    from sqlmodel import Session

    engine = create_engine(_get_db_url(), echo=False)
    return Session(engine)


def seed(setup_complete: bool = False) -> None:
    """Truncate core tables and optionally re-seed minimal data."""
    session = _make_session()
    try:
        # ---- Truncate -------------------------------------------------------
        tables_str = ", ".join(CORE_TABLES)
        print(f"  Truncating: {tables_str}")
        session.execute(text(f"TRUNCATE TABLE {tables_str} CASCADE"))
        session.commit()
        print("  ✓ Truncate done.")

        # ---- Optionally re-seed ---------------------------------------------
        if setup_complete:
            _seed_minimal_data(session)

        print("  ✓ Seed complete.\n")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _seed_minimal_data(session) -> None:
    """Insert a minimal admin user + organization_settings row.

    The admin email/password match the defaults in the E2E smoke spec so that
    ``login-setup.ts`` can authenticate without running the First-Run wizard.
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from src.modules.identity.infrastructure.password_utils import hash_password

    org_settings_id = uuid4()
    user_id = uuid4()
    now = datetime.now(UTC)

    # ---- organization_settings row (singleton_key='default') ----------------
    print("  Seeding organization_settings …")
    session.execute(
        text("""
            INSERT INTO organization_settings
                (id, singleton_key, name, timezone,
                 allowed_domains, attendance_allowed_networks,
                 guide_progress, created_at, updated_at)
            VALUES
                (:id, :key, :name, :tz,
                 '{}'::text[], '{}'::text[],
                 '{}'::jsonb, :now, :now)
        """),
        {
            "id": org_settings_id,
            "key": "default",
            "name": "Vroom HR E2E",
            "tz": "Asia/Ho_Chi_Minh",
            "now": now,
        },
    )
    session.commit()

    # ---- admin user ---------------------------------------------------------
    print("  Seeding admin user …")
    password_hash = hash_password("VroomQA!148#2026")
    session.execute(
        text("""
            INSERT INTO users
                (id, email, name, password_hash, role,
                 must_change_password, is_active, created_at, last_login)
            VALUES
                (:id, :email, :name, :pwd, :role,
                 :must_change, :active, :now, :now)
        """),
        {
            "id": user_id,
            "email": "hr.qa@vroom.example.com",
            "name": "HR QA",
            "pwd": password_hash,
            "role": "admin",
            "must_change": False,
            "active": True,


def main() -> None:
    parser = argparse.ArgumentParser(description="E2E seed — reset DB for Playwright tests")
    parser.add_argument(
        "--setup-complete",
        action="store_true",
        help="After truncating, re-seed a minimal admin + org_settings row",
    )
    args = parser.parse_args()

    print(f"[seed_e2e] DB reset (setup_complete={args.setup_complete}) …")
    try:
        seed(setup_complete=args.setup_complete)
    except Exception as exc:
        print(f"[seed_e2e] FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
