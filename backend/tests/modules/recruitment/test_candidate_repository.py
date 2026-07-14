"""Regression tests for the Candidate repository read projection."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.recruitment.domain.entities import Candidate
from src.modules.recruitment.infrastructure.repositories import CandidateRepository


@pytest.mark.asyncio
async def test_list_candidates_does_not_select_removed_legacy_calendar_columns() -> None:
    """Candidate listing must work after scheduling fields moved to interviews."""
    session = AsyncMock()

    count_result = MagicMock()
    count_result.scalar.return_value = 0
    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = []
    session.execute.side_effect = [count_result, rows_result]

    rows, total = await CandidateRepository(session).list_candidates()

    assert rows == []
    assert total == 0
    query = str(session.execute.call_args_list[1].args[0])
    assert "calendar_event_id" not in query
    assert "interview_start_at" not in query
    assert "interview_timezone" not in query


@pytest.mark.asyncio
async def test_create_candidate_omits_removed_legacy_calendar_columns() -> None:
    """Candidate promotion must insert against the post-migration schema."""
    session = AsyncMock()
    candidate = Candidate(name="Promotion Probe", email="probe@example.com")

    created = await CandidateRepository(session).create(candidate)

    assert created is candidate
    query = str(session.execute.await_args.args[0])
    assert query.startswith("INSERT INTO candidates")
    assert "calendar_event_id" not in query
    assert "interview_start_at" not in query
    assert "interview_timezone" not in query
