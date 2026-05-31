"""Property-based test for onboarding process status filtering.

Feature: onboarding, Property 16: Status filtering returns only matching
processes

This test drives ``OnboardingService.list_processes`` with a defined status
value as a filter against a mix of stored ``OnboardingProcess`` records whose
statuses are drawn from the defined ``OnboardingStatus`` values
(``in_progress`` / ``complete``), and asserts the filtering invariant:

  * Every ``OnboardingProcess`` returned by the list has a status identical to
    the requested filter value (R6.4).
  * As a sanity check, when the number of stored processes does not exceed the
    page-size cap (50), the number of returned items equals the number of
    stored processes whose status matches the filter.

The checks are fast, pure-logic checks against in-memory fakes defined inline in
this module (no shared conftest / fakes module, to avoid collisions with the
other onboarding property-test modules). ``FakeProcessRepo.list`` faithfully
models the real repository's status filter + pagination + true-total contract,
and ``FakeTaskRepo.count_by_status`` supplies the per-process checklist counts
``list_processes`` needs to project progress.

Validates: Requirements 6.4
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.domain.entities import OnboardingProcess
from src.modules.onboarding.domain.enums import OnboardingStatus

# Page-size cap applied by the read model (R6.2). Generated process counts are
# kept at or below this so a single page=1 request returns every matching
# process, letting the test assert the exact matching count without paging.
_PAGE_SIZE_CAP = 50

# The defined onboarding status values, used both to label stored processes and
# to choose a filter value (only ever a defined status, per Property 16).
_DEFINED_STATUSES: list[str] = [status.value for status in OnboardingStatus]


# ---------------------------------------------------------------------------
# In-memory fakes (inline, module-private — no shared fixtures)
# ---------------------------------------------------------------------------
class FakeProcessRepo:
    """Stores processes; ``list`` filters by exact status and paginates.

    Mirrors the real ``OnboardingProcessRepository.list`` contract: when a
    ``status`` filter is supplied only processes whose status is identical to
    it are considered, the returned ``total`` is the true count of matching
    processes (ignoring pagination), and the page slice is derived from
    ``(page - 1) * page_size`` with a ``page_size`` limit.
    """

    def __init__(self, processes: list[OnboardingProcess]) -> None:
        self.processes = processes

    async def list(
        self,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[OnboardingProcess], int]:
        matching = [
            process for process in self.processes if status is None or process.status == status
        ]
        total = len(matching)
        offset = (page - 1) * page_size
        page_slice = matching[offset : offset + page_size]
        return page_slice, total


class FakeTaskRepo:
    """Supplies per-process checklist counts for the progress projection.

    ``count_by_status`` returns a simple mapping for each stored process; the
    exact counts are irrelevant to status filtering (Property 16 only inspects
    each returned item's ``status``), so an empty mapping is sufficient and
    faithful to a process whose tasks are not the subject of this test.
    """

    async def count_by_status(self, process_id: UUID) -> dict[str, int]:
        return {}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def _build_service(statuses: list[str]) -> OnboardingService:
    """Build a service over processes labelled with the given statuses."""
    processes = [
        OnboardingProcess(
            candidate_id=uuid4(),
            employee_id=uuid4(),
            status=status,
        )
        for status in statuses
    ]
    return OnboardingService(
        process_repo=FakeProcessRepo(processes),  # type: ignore[arg-type]
        task_repo=FakeTaskRepo(),  # type: ignore[arg-type]
        audit_repo=None,  # type: ignore[arg-type]
        employee_repo=None,  # type: ignore[arg-type]
        session=None,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------
# Feature: onboarding, Property 16: Status filtering returns only matching
# processes
@settings(max_examples=200, deadline=None)
@given(
    statuses=st.lists(
        st.sampled_from(_DEFINED_STATUSES),
        min_size=0,
        max_size=_PAGE_SIZE_CAP,
    ),
    chosen=st.sampled_from(list(OnboardingStatus)),
)
def test_status_filtering_returns_only_matching_processes(
    statuses: list[str],
    chosen: OnboardingStatus,
) -> None:
    """Filtering by a defined status returns only processes with that status.

    Validates: Requirements 6.4
    """
    service = _build_service(statuses)
    filter_value = chosen.value

    result = asyncio.run(
        service.list_processes(status=filter_value, page=1, page_size=_PAGE_SIZE_CAP)
    )

    # R6.4: every returned process has a status identical to the filter value.
    for item in result.items:
        assert item.status == filter_value

    # Sanity: with the generated count capped at the page size, page 1 returns
    # exactly the stored processes whose status matches the filter.
    expected_match_count = sum(1 for status in statuses if status == filter_value)
    assert len(result.items) == expected_match_count
    assert result.total == expected_match_count
