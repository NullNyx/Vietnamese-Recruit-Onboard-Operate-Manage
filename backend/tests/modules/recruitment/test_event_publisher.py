"""Tests for ArqDomainEventPublisher.

Verifies the ARQ-backed domain event publisher enqueues the correct job
for candidate_accepted events and ignores unknown event types.

Requirements: runtime backbone wiring
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from arq.connections import RedisSettings

from src.modules.recruitment.infrastructure.event_publisher import (
    CANDIDATE_ACCEPTED_EVENT,
    ONBOARDING_CONSUMER_TASK,
    ArqDomainEventPublisher,
)


# ─── Constants ─────────────────────────────────────────────────────────


def test_candidate_accepted_event_constant() -> None:
    assert CANDIDATE_ACCEPTED_EVENT == "candidate_accepted"


def test_onboarding_consumer_task_constant() -> None:
    assert ONBOARDING_CONSUMER_TASK == "process_candidate_accepted"


# ─── Publisher level ───────────────────────────────────────────────────


@pytest.fixture
def fake_pool() -> AsyncMock:
    pool = AsyncMock()
    pool.enqueue_job = AsyncMock()
    return pool


@pytest.fixture
def publisher(fake_pool: AsyncMock) -> ArqDomainEventPublisher:
    return ArqDomainEventPublisher(redis_settings=RedisSettings(), pool=fake_pool)


async def test_publish_candidate_accepted_enqueues_job(
    publisher: ArqDomainEventPublisher, fake_pool: AsyncMock
) -> None:
    """publish(candidate_accepted) enqueues one process_candidate_accepted job."""
    payload = {
        "candidate_id": str(uuid4()),
        "name": "Nguyen Van A",
        "email": "candidate@example.com",
    }

    await publisher.publish(event_type=CANDIDATE_ACCEPTED_EVENT, payload=payload)

    fake_pool.enqueue_job.assert_awaited_once_with(ONBOARDING_CONSUMER_TASK, payload)


async def test_publish_forwards_payload_unchanged(
    publisher: ArqDomainEventPublisher, fake_pool: AsyncMock
) -> None:
    """The enqueued payload is forwarded unchanged."""
    payload = {
        "candidate_id": str(uuid4()),
        "name": "Tran Thi B",
        "email": "tran.b@example.com",
    }

    await publisher.publish(event_type=CANDIDATE_ACCEPTED_EVENT, payload=payload)

    args, _ = fake_pool.enqueue_job.call_args
    enqueued_name, enqueued_payload = args
    assert enqueued_name == ONBOARDING_CONSUMER_TASK
    assert enqueued_payload == payload
    assert set(enqueued_payload) == {"candidate_id", "name", "email"}


async def test_publish_non_candidate_accepted_event_is_noop(
    publisher: ArqDomainEventPublisher, fake_pool: AsyncMock
) -> None:
    """A different event type enqueues nothing."""
    await publisher.publish(
        event_type="interview_scheduled",
        payload={"candidate_id": str(uuid4())},
    )

    fake_pool.enqueue_job.assert_not_awaited()
