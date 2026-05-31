"""Migration smoke test for the interview calendar fields (revision 029).

This is an integration test: it spins up a real PostgreSQL 15 instance with
``testcontainers``, runs ``alembic upgrade head`` against it, and verifies that
migration 029 (``029_add_interview_calendar_fields``) realizes ADR-0008 at the
schema level:

1. The three interview columns exist on the existing ``candidates`` table —
   ``calendar_event_id``, ``interview_start_at``, ``interview_timezone`` —
   so a Candidate can carry its single interview's Google Calendar reference
   and time without a separate interview entity (R4.1, R4.2, R4.3).
2. The single-row ``organization_settings`` table exists (the canonical
   timezone source of truth, R11.1).
3. No separate interview table was created — the one-interview-per-Candidate
   model adds columns to ``candidates`` rather than a new entity (R4.5).

The test reuses the project's real Alembic environment (``backend/alembic`` +
``alembic.ini``), driving the async (asyncpg) engine that ``env.py`` builds via
the ``DATABASE_URL`` override, exactly as production migrations run. It mirrors
the onboarding migration smoke test (``test_migration.py``): a module-scoped
container + ``alembic upgrade head``, and skips cleanly when
``testcontainers``/``docker`` or a running Docker daemon is unavailable.

Requirements: 4.5
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

# testcontainers / docker are integration-only dependencies. Skip the whole
# module cleanly if either the library or a running Docker daemon is absent.
docker = pytest.importorskip("docker")
PostgresContainer = pytest.importorskip("testcontainers.postgres").PostgresContainer

# backend/ — the directory that holds alembic.ini and the alembic/ package.
# test file: backend/tests/modules/recruitment/test_interview_migration.py
BACKEND_DIR = Path(__file__).resolve().parents[3]

# The three interview columns migration 029 adds to ``candidates`` (R4.1–R4.3).
INTERVIEW_COLUMNS = {
    "calendar_event_id",
    "interview_start_at",
    "interview_timezone",
}


def _docker_available() -> bool:
    """Return True if a Docker daemon is reachable, else False."""
    try:
        client = docker.from_env()
        client.ping()
    except Exception:  # noqa: BLE001 - any docker error means "not available"
        return False
    return True


def _run_alembic_upgrade_head(async_url: str) -> None:
    """Run ``alembic upgrade head`` against ``async_url`` using the real env.

    ``env.py`` reads ``DATABASE_URL`` from the environment and builds an async
    (asyncpg) engine, so we point that variable at the container and invoke the
    Alembic command API the same way the CLI would.
    """
    from alembic.config import Config

    from alembic import command

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", async_url)

    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = async_url
    try:
        command.upgrade(config, "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest.fixture(scope="module")
def migrated_engine() -> Iterator[Engine]:
    """Start PostgreSQL 15, apply all migrations to head, yield a sync engine.

    Module-scoped so the (slow) container start + full migration chain runs
    once for every test in this module.
    """
    if not _docker_available():
        pytest.skip("Docker is not available for the migration smoke test")

    with PostgresContainer("postgres:15-alpine") as postgres:
        # testcontainers returns a psycopg2 URL; derive the asyncpg variant that
        # the Alembic env.py expects for its async engine.
        sync_url = postgres.get_connection_url()
        async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

        _run_alembic_upgrade_head(async_url)

        engine = create_engine(sync_url)
        try:
            yield engine
        finally:
            engine.dispose()


@pytest.mark.integration
def test_migration_adds_interview_columns_to_candidates(
    migrated_engine: Engine,
) -> None:
    """`alembic upgrade head` adds the three interview columns to ``candidates``.

    Requirements: 4.5
    """
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())

    assert "candidates" in tables, "candidates table is missing"

    columns = {col["name"] for col in inspector.get_columns("candidates")}
    missing = INTERVIEW_COLUMNS - columns
    assert not missing, f"migration did not add interview columns: {missing}"


@pytest.mark.integration
def test_migration_creates_organization_settings_table(
    migrated_engine: Engine,
) -> None:
    """`alembic upgrade head` creates the single-row ``organization_settings`` table.

    Requirements: 4.5
    """
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())

    assert "organization_settings" in tables, "organization_settings table is missing"


@pytest.mark.integration
def test_migration_creates_no_separate_interview_table(
    migrated_engine: Engine,
) -> None:
    """No separate interview entity is introduced (one-interview-per-Candidate).

    ADR-0008 stores the interview's Calendar reference on the existing
    ``candidates`` row, so the migration must not create any standalone
    interview table.

    Requirements: 4.5
    """
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())

    interview_tables = {name for name in tables if "interview" in name.lower()}
    assert not interview_tables, f"migration created a separate interview table: {interview_tables}"
