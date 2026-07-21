"""ARQ-backed domain event publisher for the recruitment module.

Bridges the recruitment ``DomainEventPublisher`` protocol (defined in
``recruitment.application.candidate_service``) to the shared ARQ task queue.
When ``CandidateService.accept_candidate`` emits the ``candidate_accepted``
domain event, this publisher enqueues a ``process_candidate_accepted`` ARQ job
that the onboarding worker consumes, closing the backbone flow
(recruitment → onboarding).

Placement rationale: the publisher *contract* is owned by the recruitment
module (it is the side that publishes), so the concrete implementation lives in
``recruitment/infrastructure`` alongside the module's other external-system
clients (MinIO, LLM, OCR). The job is enqueued by its registered task-function
*name* (a plain string), never by importing the onboarding task function, so
the recruitment module never imports the onboarding module and no circular
import is introduced.

Requirements: 1.1
"""

from __future__ import annotations

import logging
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

logger = logging.getLogger(__name__)

# Domain event type emitted by ``CandidateService.accept_candidate``.
CANDIDATE_ACCEPTED_EVENT = "candidate_accepted"

# ARQ task-function name registered by the onboarding worker's get_arq_tasks().
# Enqueued by name (string) to avoid importing the onboarding module.
ONBOARDING_CONSUMER_TASK = "process_candidate_accepted"


class ArqDomainEventPublisher:
    """Concrete ``DomainEventPublisher`` that enqueues ARQ jobs.

    Implements the ``DomainEventPublisher`` protocol from
    ``recruitment.application.candidate_service``. For the ``candidate_accepted``
    event it enqueues a ``process_candidate_accepted`` ARQ job carrying the
    unchanged payload (``candidate_id``, ``name``, ``email``). Other event types
    are ignored (no-op): the publisher is a fire-and-forget bridge, and the
    emitting service has already committed its own state before publishing, so
    an unrouted event type is not an error.

    The ARQ redis pool is created lazily on the first publish and cached, so
    importing this module (and the recruitment container) never opens a Redis
    connection.

    Args:
        redis_settings: Connection settings for the ARQ Redis instance.
        pool: An existing ``ArqRedis`` pool to reuse (primarily for tests). When
            omitted, a pool is created lazily from ``redis_settings``.
    """

    def __init__(
        self,
        redis_settings: RedisSettings,
        pool: ArqRedis | None = None,
    ) -> None:
        self._redis_settings = redis_settings
        self._pool = pool

    async def _get_pool(self) -> ArqRedis:
        """Return the ARQ pool, creating and caching it on first use."""
        if self._pool is None:
            self._pool = await create_pool(self._redis_settings, default_queue_name="onboarding-worker")
        return self._pool

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a domain event by enqueuing its matching ARQ job.

        Args:
            event_type: The domain event type. Only ``candidate_accepted`` is
                routed to the onboarding consumer; other types are ignored.
            payload: The event payload. For ``candidate_accepted`` this carries
                ``candidate_id``, ``name``, and ``email`` and is forwarded to the
                ``process_candidate_accepted`` job unchanged.
        """
        if event_type != CANDIDATE_ACCEPTED_EVENT:
            # No downstream ARQ consumer is wired for other event types.
            return

        pool = await self._get_pool()
        await pool.enqueue_job(ONBOARDING_CONSUMER_TASK, payload)
        logger.info(
            "Enqueued %s job for candidate_accepted event (candidate_id=%s)",
            ONBOARDING_CONSUMER_TASK,
            payload.get("candidate_id"),
        )
