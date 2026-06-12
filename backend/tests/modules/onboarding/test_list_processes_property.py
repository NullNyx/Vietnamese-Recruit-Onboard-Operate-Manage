"""Property-based test for the onboarding process list read model.

Feature: onboarding, Property 15: The process list reports accurate progress,
is capped, and reports the true total

This module drives :meth:`OnboardingService.list_processes` over arbitrary sets
of stored ``OnboardingProcess`` records (each with its own checklist of done /
pending tasks, including zero-task processes) and arbitrary page / page_size /
status-filter requests, asserting that:

  * each returned list item exposes its process status, its linked employee id,
    a ``completed_count`` equal to its number of ``done`` tasks, and a
    ``total_count`` equal to its number of tasks (R6.1);
  * the response holds at most 50 items (the pagination cap) and never more
    than the effective page size (R6.2);
  * ``total`` equals the number of processes matching the (optional) status
    filter, regardless of pagination; and
  * when no process matches the request, ``items`` is empty and ``total`` is 0.

The test runs the real :class:`OnboardingService` against in-memory fakes
defined inline in this module (no shared conftest / fakes module, to avoid
colliding with the other onboarding property-test modules). The fakes mirror
the real repository semantics ``list_processes`` depends on: the process
repository filters by status, computes the true total, orders by ``created_at``
descending, and applies offset / limit pagination; the task repository returns
per-process status counts from the stored tasks.

Validates: Requirements 6.1, 6.2
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.domain.entities import OnboardingProcess, OnboardingTask
from src.modules.onboarding.domain.enums import OnboardingStatus, OnboardingTaskStatus

# The pagination cap enforced by the read model (R6.2).
_PAGE_SIZE_MAX = 50

# Upper bound on the number of processes generated per world. Comfortably
# exceeds the 50-item cap so a single page can be forced to truncate.
_MAX_PROCESSES = 80

# Upper bound on the number of done / pending tasks generated per process. The
# minimum of 0 exercises the zero-task process (total_count == 0).
_MAX_TASKS_PER_BUCKET = 4

# The two defined process statuses, used both as stored values and filters.
_STATUS_VALUES = [OnboardingStatus.IN_PROGRESS.value, OnboardingStatus.COMPLETE.value]


# ---------------------------------------------------------------------------
# In-memory fakes (inline, module-private — no shared fixtures)
# ---------------------------------------------------------------------------
class FakeProcessRepo:
    """In-memory OnboardingProcess store mirroring the real ``list`` semantics.

    Stores a flat list of processes. ``list`` applies the optional status
    filter, computes the true total of matching processes (ignoring
    pagination), orders the matches by ``created_at`` descending (as the real
    repository does), then applies offset / limit pagination for the requested
    page.
    """

    def __init__(self, processes: list[OnboardingProcess]) -> None:
        self.processes = processes

    async def list(
        self,
        status: str | None = None,
        page: int = 1,
        page_size: int = _PAGE_SIZE_MAX,
    ) -> tuple[list[OnboardingProcess], int]:
        filtered = [p for p in self.processes if status is None or p.status == status]
        total = len(filtered)
        ordered = sorted(filtered, key=lambda p: p.created_at, reverse=True)
        offset = (page - 1) * page_size
        page_rows = ordered[offset : offset + page_size]
        return page_rows, total


class FakeTaskRepo:
    """In-memory OnboardingTask store returning per-process status counts.

    ``count_by_status`` groups the stored tasks for one process by status,
    yielding an empty mapping for a process that has no tasks (matching the real
    repository, where a zero-task process produces no rows).
    """

    def __init__(self, tasks: list[OnboardingTask]) -> None:
        self.tasks = tasks

    async def count_by_status(self, process_id: UUID) -> dict[str, int]:
        counts: dict[str, int] = {}
        for task in self.tasks:
            if task.process_id == process_id:
                counts[task.status] = counts.get(task.status, 0) + 1
        return counts

    async def count_by_status_for_processes(self, process_ids: list[UUID]) -> dict[UUID, dict[str, int]]:
        counts_by_process: dict[UUID, dict[str, int]] = {pid: {} for pid in process_ids}
        for task in self.tasks:
            if task.process_id in counts_by_process:
                counts_by_process[task.process_id][task.status] = counts_by_process[task.process_id].get(task.status, 0) + 1
        return counts_by_process


class _UnusedRepo:
    """Placeholder for repositories ``list_processes`` never touches."""


class _UnusedSession:
    """Placeholder for the session ``list_processes`` never touches."""


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
# A process spec: (status, done_count, pending_count). Varying counts (including
# zero of both) exercises empty, partial, and fully-complete checklists.
_process_spec = st.tuples(
    st.sampled_from(_STATUS_VALUES),
    st.integers(min_value=0, max_value=_MAX_TASKS_PER_BUCKET),
    st.integers(min_value=0, max_value=_MAX_TASKS_PER_BUCKET),
)


@st.composite
def _requests(draw: st.DrawFn) -> tuple[list[tuple[str, int, int]], str | None, int, int]:
    """Draw a world of process specs plus a page / page_size / status filter.

    ``page_size`` ranges below 1 and above the 50 cap to exercise the service's
    clamping to ``[1, 50]``; ``page`` ranges below 1 to exercise clamping to 1
    and beyond the populated pages to exercise empty pages. The status filter is
    ``None`` (no filter), a defined status, or — implicitly via empty worlds —
    matches nothing.
    """
    specs = draw(st.lists(_process_spec, min_size=0, max_size=_MAX_PROCESSES))
    status_filter = draw(st.sampled_from([None, *_STATUS_VALUES]))
    page = draw(st.integers(min_value=-2, max_value=8))
    page_size = draw(st.integers(min_value=-5, max_value=120))
    return specs, status_filter, page, page_size


# ---------------------------------------------------------------------------
# Async driver
# ---------------------------------------------------------------------------
def _build_world(
    specs: list[tuple[str, int, int]],
) -> tuple[list[OnboardingProcess], list[OnboardingTask], dict[UUID, dict[str, object]]]:
    """Build processes + tasks from specs and an expectation map per process.

    Each process gets a distinct ``created_at`` (by index) so the
    ``created_at``-descending ordering is unambiguous, a fresh ``employee_id``,
    and a checklist of ``done_count`` done + ``pending_count`` pending tasks.
    The returned map records, per process id, the expected status, employee id,
    completed count, and total count for assertion.
    """
    base = datetime(2024, 1, 1, tzinfo=UTC)
    processes: list[OnboardingProcess] = []
    tasks: list[OnboardingTask] = []
    expected: dict[UUID, dict[str, object]] = {}

    for index, (status, done_count, pending_count) in enumerate(specs):
        employee_id = uuid4()
        process = OnboardingProcess(
            candidate_id=uuid4(),
            employee_id=employee_id,
            status=status,
        )
        process.created_at = base + timedelta(seconds=index)
        processes.append(process)

        order_index = 0
        for _ in range(done_count):
            tasks.append(
                OnboardingTask(
                    process_id=process.id,
                    task_key=f"task_{order_index}",
                    name=f"Task {order_index}",
                    status=OnboardingTaskStatus.DONE.value,
                    order_index=order_index,
                )
            )
            order_index += 1
        for _ in range(pending_count):
            tasks.append(
                OnboardingTask(
                    process_id=process.id,
                    task_key=f"task_{order_index}",
                    name=f"Task {order_index}",
                    status=OnboardingTaskStatus.PENDING.value,
                    order_index=order_index,
                )
            )
            order_index += 1

        expected[process.id] = {
            "status": status,
            "employee_id": employee_id,
            "completed_count": done_count,
            "total_count": done_count + pending_count,
        }

    return processes, tasks, expected


async def _run_list_property(
    specs: list[tuple[str, int, int]],
    status_filter: str | None,
    page: int,
    page_size: int,
) -> None:
    """List processes for the request and assert the Property 15 invariants."""
    processes, tasks, expected = _build_world(specs)

    service = OnboardingService(
        process_repo=FakeProcessRepo(processes),  # type: ignore[arg-type]
        task_repo=FakeTaskRepo(tasks),  # type: ignore[arg-type]
        audit_repo=_UnusedRepo(),  # type: ignore[arg-type]
        employee_repo=_UnusedRepo(),  # type: ignore[arg-type]
        session=_UnusedSession(),  # type: ignore[arg-type]
    )

    result = await service.list_processes(status=status_filter, page=page, page_size=page_size)

    # Effective clamping the service applies (page >= 1, page_size in [1, 50]).
    effective_page = max(page, 1)
    effective_page_size = max(1, min(page_size, _PAGE_SIZE_MAX))
    assert result.page == effective_page
    assert result.page_size == effective_page_size

    # The true total equals the number of processes matching the status filter.
    matching = [p for p in processes if status_filter is None or p.status == status_filter]
    expected_total = len(matching)
    assert result.total == expected_total

    # The response is capped at 50 items and never exceeds the effective page.
    assert len(result.items) <= _PAGE_SIZE_MAX
    assert len(result.items) <= effective_page_size

    # The returned page is exactly the created_at-desc slice for the request.
    ordered = sorted(matching, key=lambda p: p.created_at, reverse=True)
    offset = (effective_page - 1) * effective_page_size
    expected_slice_ids = [p.id for p in ordered[offset : offset + effective_page_size]]
    assert [item.process_id for item in result.items] == expected_slice_ids

    # Each returned item exposes accurate status, employee id, and progress.
    for item in result.items:
        exp = expected[item.process_id]
        assert item.status == exp["status"]
        assert item.employee_id == exp["employee_id"]
        assert item.completed_count == exp["completed_count"]
        assert item.total_count == exp["total_count"]

    # No process matches -> empty list with a zero total.
    if expected_total == 0:
        assert result.items == []
        assert result.total == 0


# Feature: onboarding, Property 15: The process list reports accurate progress,
# is capped, and reports the true total
@settings(max_examples=200, deadline=None)
@given(request=_requests())
def test_list_processes_reports_accurate_progress_cap_and_total(
    request: tuple[list[tuple[str, int, int]], str | None, int, int],
) -> None:
    """The process list is accurate, capped at 50, and reports the true total.

    Validates: Requirements 6.1, 6.2
    """
    specs, status_filter, page, page_size = request
    asyncio.run(_run_list_property(specs, status_filter, page, page_size))
