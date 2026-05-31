"""Integration test for the recruitment publisher → onboarding consumer boundary.

Verifies the recruitment-side ``ArqDomainEventPublisher`` enqueues exactly one
``process_candidate_accepted`` ARQ job carrying the correct payload when a
Candidate is accepted, closing the backbone flow (recruitment → onboarding).

Two layers are exercised:

* Publisher level: ``ArqDomainEventPublisher.publish`` with an injected fake
  ARQ pool — asserts exactly one ``enqueue_job`` call with the job name and the
  unchanged payload, and that non-``candidate_accepted`` events are a no-op.
* Service level: ``CandidateService.accept_candidate`` wired with the real
  ``ArqDomainEventPublisher`` (fake pool) — asserts the accept flow enqueues
  exactly one job whose payload (``candidate_id``, ``name``, ``email``) is the
  one the service builds.

Requirements: 1.1
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from arq.connections import RedisSettings

from src.modules.recruitment.application.candidate_service import CandidateService
from src.modules.recruitment.domain.entities import Candidate
from src.modules.recruitment.domain.enums import CandidateStatus
from src.modules.recruitment.infrastructure.event_publisher import (
    CANDIDATE_ACCEPTED_EVENT,
    ONBOARDING_CONSUMER_TASK,
    ArqDomainEventPublisher,
)

# ─── Helpers / Fixtures ────────────────────────────────────────────────


@pytest.fixture
def fake_pool() -> AsyncMock:
    """Fake ArqRedis pool recording ``enqueue_job(name, payload)`` calls."""
    pool = AsyncMock()
    pool.enqueue_job = AsyncMock()
    return pool


@pytest.fixture
def publisher(fake_pool: AsyncMock) -> ArqDomainEventPublisher:
    """Publisher with the fake pool injected (no real Redis connection)."""
    return ArqDomainEventPublisher(redis_settings=RedisSettings(), pool=fake_pool)


def _make_candidate(
    status: str = CandidateStatus.INTERVIEW_SCHEDULED,
    email: str = "candidate@example.com",
) -> Candidate:
    """Build a minimal Candidate eligible for acceptance."""
    return Candidate(
        id=uuid4(),
        name="Nguyen Van A",
        email=email,
        phone="0901234567",
        skills=["Python"],
        experience=[],
        education=[],
        summary="Test candidate",
        status=status,
        confidence_score=0.85,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_candidate_service(
    candidate: Candidate, publisher: ArqDomainEventPublisher
) -> tuple[CandidateService, AsyncMock]:
    """Build a CandidateService with mocked deps and the real publisher wired."""
    candidate_repo = AsyncMock()
    candidate_repo.get_by_id = AsyncMock(return_value=candidate)
    candidate_repo.update = AsyncMock(side_effect=lambda c: c)

    session = AsyncMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    # ``session.add`` is synchronous in real SQLAlchemy; keep it non-async so
    # the audit helper's ``session.add(...)`` does not create a stray coroutine.
    session.add = MagicMock()

    service = CandidateService(
        candidate_repo=candidate_repo,
        cv_document_repo=AsyncMock(),
        minio_client=AsyncMock(),
        session=session,
        event_publisher=publisher,
        user_id=uuid4(),
    )
    return service, candidate_repo


# ─── Constant sanity ───────────────────────────────────────────────────


def test_job_name_constant_matches_consumer_task() -> None:
    """The enqueued job name is the onboarding consumer's registered name."""
    assert ONBOARDING_CONSUMER_TASK == "process_candidate_accepted"
    assert CANDIDATE_ACCEPTED_EVENT == "candidate_accepted"


# ─── Publisher level: exactly one enqueue with the correct payload ──────


async def test_publish_candidate_accepted_enqueues_exactly_one_job(
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
    """The enqueued payload is forwarded unchanged (candidate_id/name/email)."""
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
    """A different event type enqueues nothing (no downstream consumer)."""
    await publisher.publish(
        event_type="interview_scheduled",
        payload={"candidate_id": str(uuid4())},
    )

    fake_pool.enqueue_job.assert_not_awaited()


# ─── Service level: accept_candidate → publisher → exactly one enqueue ──


async def test_accept_candidate_enqueues_one_job_with_service_payload(
    publisher: ArqDomainEventPublisher, fake_pool: AsyncMock
) -> None:
    """Accepting a candidate enqueues exactly one job with the built payload."""
    candidate = _make_candidate()
    service, _ = _make_candidate_service(candidate, publisher)

    await service.accept_candidate(candidate.id)

    expected_payload = {
        "candidate_id": str(candidate.id),
        "name": candidate.name,
        "email": candidate.email,
    }
    fake_pool.enqueue_job.assert_awaited_once_with(ONBOARDING_CONSUMER_TASK, expected_payload)
