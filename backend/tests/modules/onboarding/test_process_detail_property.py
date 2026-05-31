"""Property-based test for the process-detail read model.

Feature: onboarding, Property 17: Process detail returns the complete checklist

This module drives ``OnboardingService.get_process`` for an arbitrary existing
``OnboardingProcess`` and asserts that requesting it by id returns each of its
tasks with the task's name and current status, matching the stored checklist
exactly. Concretely, for any stored process plus checklist the returned
:class:`ProcessDetail`:

  * exposes the same number of tasks as were stored;
  * returns each task (matched by id) with the same name and status as stored;
  * orders the tasks by ``order_index`` ascending;
  * echoes the process's ``status`` and linked ``employee_id``; and
  * reports ``completed_count`` equal to the number of ``done`` tasks and
    ``total_count`` equal to the number of tasks.

A separate example test asserts that requesting an unknown id raises
:class:`OnboardingProcessNotFoundError` (R6.6).

The checks are fast, pure-logic checks against in-memory fakes defined inline in
this module (no shared conftest / fakes module, to avoid collisions with the
other onboarding property-test modules). The fakes faithfully model the only
repository contracts ``get_process`` depends on: ``OnboardingProcessRepository.
get_by_id`` and ``OnboardingTaskRepository.list_by_process`` (ordered by
``order_index``).

Validates: Requirements 6.3
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.modules.onboarding.application.onboarding_service import (
    OnboardingService,
    ProcessDetail,
)
from src.modules.onboarding.domain.entities import OnboardingProcess, OnboardingTask
from src.modules.onboarding.domain.enums import OnboardingStatus, OnboardingTaskStatus
from src.modules.onboarding.domain.exceptions import OnboardingProcessNotFoundError

# Upper bound on the number of tasks generated per process. Includes 0 so a
# zero-task process is exercised, and goes beyond the canonical four-task
# checklist to stress arbitrary task counts.
_MAX_TASKS = 6

# Printable ASCII excluding the space so generated task names are non-empty.
_NAME_ALPHABET = st.characters(min_codepoint=33, max_codepoint=126)

# The two defined task statuses, as their stored string values.
_TASK_STATUS_VALUES = [OnboardingTaskStatus.PENDING.value, OnboardingTaskStatus.DONE.value]

# The two defined process statuses, as their stored string values.
_PROCESS_STATUS_VALUES = [OnboardingStatus.IN_PROGRESS.value, OnboardingStatus.COMPLETE.value]


# ---------------------------------------------------------------------------
# In-memory fakes (inline, module-private — no shared fixtures)
# ---------------------------------------------------------------------------
class FakeProcessRepo:
    """Stores a single process; ``get_by_id`` returns it or ``None``."""

    def __init__(self, process: OnboardingProcess | None) -> None:
        self._process = process

    async def get_by_id(self, process_id: UUID) -> OnboardingProcess | None:
        if self._process is not None and self._process.id == process_id:
            return self._process
        return None


class FakeTaskRepo:
    """Stores the checklist tasks; ``list_by_process`` returns them ordered.

    Mirrors the real repository contract: tasks for the requested process are
    returned sorted by ``order_index`` ascending (tasks for other processes are
    excluded).
    """

    def __init__(self, tasks: list[OnboardingTask]) -> None:
        self._tasks = tasks

    async def list_by_process(self, process_id: UUID) -> list[OnboardingTask]:
        return sorted(
            (task for task in self._tasks if task.process_id == process_id),
            key=lambda task: task.order_index,
        )


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def _build_service(
    process: OnboardingProcess | None,
    tasks: list[OnboardingTask],
) -> OnboardingService:
    """Build a service wired with only the repos ``get_process`` touches.

    ``get_process`` reads exclusively from the process and task repositories, so
    the audit repo, employee repo, and session are unused and supplied as
    ``None``.
    """
    return OnboardingService(
        process_repo=FakeProcessRepo(process),  # type: ignore[arg-type]
        task_repo=FakeTaskRepo(tasks),  # type: ignore[arg-type]
        audit_repo=None,  # type: ignore[arg-type]
        employee_repo=None,  # type: ignore[arg-type]
        session=None,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
@st.composite
def _checklists(draw: st.DrawFn, process_id: UUID) -> list[OnboardingTask]:
    """Build a checklist of tasks with unique order_index and varied state.

    Each task carries an arbitrary non-empty display name (1-100 chars, within
    the entity bound) and a status drawn from ``{pending, done}``. The
    ``order_index`` values are unique across the checklist (the fixed checklist
    has distinct positions), and the tasks are generated in a shuffled order so
    the test exercises the repository's ordering rather than insertion order.
    """
    count = draw(st.integers(min_value=0, max_value=_MAX_TASKS))
    order_indices = draw(
        st.lists(
            st.integers(min_value=0, max_value=1000),
            unique=True,
            min_size=count,
            max_size=count,
        )
    )
    tasks: list[OnboardingTask] = []
    for order_index in order_indices:
        name = draw(st.text(alphabet=_NAME_ALPHABET, min_size=1, max_size=100))
        status = draw(st.sampled_from(_TASK_STATUS_VALUES))
        tasks.append(
            OnboardingTask(
                process_id=process_id,
                task_key=f"task_{order_index}",
                name=name,
                status=status,
                order_index=order_index,
            )
        )
    return tasks


@st.composite
def _worlds(draw: st.DrawFn) -> tuple[OnboardingProcess, list[OnboardingTask]]:
    """Draw an existing process plus its stored checklist of tasks."""
    process = OnboardingProcess(
        candidate_id=draw(st.uuids()),
        employee_id=draw(st.uuids()),
        status=draw(st.sampled_from(_PROCESS_STATUS_VALUES)),
    )
    tasks = draw(_checklists(process.id))
    return process, tasks


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------
async def _get_detail(
    process: OnboardingProcess,
    tasks: list[OnboardingTask],
) -> ProcessDetail:
    """Build the service and fetch the process detail by id."""
    service = _build_service(process, tasks)
    return await service.get_process(process.id)


# Feature: onboarding, Property 17: Process detail returns the complete checklist
@settings(max_examples=200, deadline=None)
@given(world=_worlds())
def test_process_detail_returns_the_complete_checklist(
    world: tuple[OnboardingProcess, list[OnboardingTask]],
) -> None:
    """Detail returns every stored task with matching name/status, in order.

    Validates: Requirements 6.3
    """
    process, tasks = world

    detail = asyncio.run(_get_detail(process, tasks))

    # Summary fields echo the stored process.
    assert detail.process_id == process.id
    assert detail.status == process.status
    assert detail.employee_id == process.employee_id

    # The checklist size matches exactly.
    assert len(detail.tasks) == len(tasks)
    assert detail.total_count == len(tasks)

    # Each returned task (matched by id) carries the stored name and status.
    stored_by_id = {task.id: task for task in tasks}
    assert {t.id for t in detail.tasks} == set(stored_by_id)
    for returned in detail.tasks:
        stored = stored_by_id[returned.id]
        assert returned.name == stored.name
        assert returned.status == stored.status
        assert returned.order_index == stored.order_index

    # Tasks are returned in ascending order_index order.
    returned_order = [t.order_index for t in detail.tasks]
    assert returned_order == sorted(returned_order)

    # Progress counts reflect the stored checklist exactly.
    expected_done = sum(1 for task in tasks if task.status == OnboardingTaskStatus.DONE.value)
    assert detail.completed_count == expected_done
    assert detail.total_count - detail.completed_count == len(tasks) - expected_done


# ---------------------------------------------------------------------------
# Example: unknown id raises not-found (R6.6)
# ---------------------------------------------------------------------------
def test_get_process_raises_for_unknown_id() -> None:
    """Requesting a process id that does not exist raises a not-found error.

    Validates: Requirements 6.3 (boundary), 6.6
    """
    # A repo holding no process: every lookup misses.
    service = _build_service(process=None, tasks=[])

    with pytest.raises(OnboardingProcessNotFoundError):
        asyncio.run(service.get_process(uuid4()))
