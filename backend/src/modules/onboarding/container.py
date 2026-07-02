"""Dependency wiring and ARQ consumer for the Onboarding module.

This file currently hosts the ARQ consumer side of the onboarding module:
the :func:`process_candidate_accepted` task function that receives the
``candidate_accepted`` event and drives :class:`OnboardingService`, plus
:func:`get_arq_tasks` which exposes the task list for worker registration.

The FastAPI ``Depends`` provider for the onboarding service
(:func:`get_onboarding_service`) is defined here as well, so the API router
(``api/router.py``) can wire its endpoints against a stable entry point. The
onboarding router and its error handlers are registered with the main app in
``src/main.py`` (alongside the other modules), and the onboarding entities are
imported in ``alembic/env.py`` so ``SQLModel.metadata`` sees them. The router
depends only on :func:`get_onboarding_service`, which builds the repositories
internally (mirroring the recruitment module), so no per-repository ``Depends``
providers are exposed.

Consumer behavior
------------------
``process_candidate_accepted`` follows the design's "Event consumption
sequence":

1. **Validate** the payload via
   :func:`~src.modules.onboarding.application.validators.validate_event_payload`
   (which maps the recruitment event key ``name`` to the Employee
   ``full_name``). A malformed/invalid event is *rejected*: a rejection audit
   entry is written in its own committed transaction and the service is **never
   called** (R1.6, R2.6). The event is not retried — a malformed payload can
   never become valid.
2. **Process** a valid event by building an :class:`OnboardingService` from a
   fresh session (created by the worker-provided ``session_maker``) and calling
   :meth:`OnboardingService.start_from_event`. ``start_from_event`` owns its
   transaction and rolls back on any failure so nothing partial persists (R1.5).
3. **Retry / final failure.** Transient errors (DB errors, etc.) propagate so
   ARQ retries the job up to ``max_tries`` (= 3, set on the worker, R1.7). On
   the *final* attempt the consumer records a failure audit entry (best effort,
   in its own committed transaction) before re-raising so the failure stays
   visible to ARQ (R1.5, R1.7).

Event identifier
-----------------
Each audit entry records an ``event_id``. It is resolved by
:func:`_resolve_event_id`, which prefers ARQ's ``ctx["job_id"]`` (stable across
retries of the same job, so every redelivery references the same event), then
falls back to an ``event_id`` / ``id`` field in the payload, and finally
generates a UUID so an entry is always attributable.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.modules.employee.infrastructure.contract_repository import ContractRepository
from src.modules.employee.infrastructure.document_repository import DocumentRepository
from src.modules.employee.infrastructure.employee_repository import EmployeeRepository
from src.modules.identity.container import get_db_session
from src.modules.onboarding.application.onboarding_service import OnboardingService
from src.modules.onboarding.application.validators import (
    ValidatedEventPayload,
    validate_event_payload,
)
from src.modules.onboarding.domain.entities import OnboardingAuditLog
from src.modules.onboarding.domain.exceptions import InvalidEventPayloadError
from src.modules.onboarding.infrastructure.audit_repository import OnboardingAuditRepository
from src.modules.onboarding.infrastructure.contract_repository import OnboardingContractRepository
from src.modules.onboarding.infrastructure.document_repository import OnboardingDocumentRepository
from src.modules.onboarding.infrastructure.process_repository import OnboardingProcessRepository
from src.modules.onboarding.infrastructure.task_repository import OnboardingTaskRepository

logger = logging.getLogger(__name__)

# Maximum ARQ attempts for the consumer job. Mirrors
# ``OnboardingWorkerSettings.max_tries`` (set by the worker, task 12.2) so the
# consumer can detect the final attempt even though ARQ does not place
# ``max_tries`` in the job ``ctx``. Used only as a fallback when
# ``ctx["max_tries"]`` is absent (R1.7).
_MAX_TRIES = 3

# Audit ``operation_type`` values written by the consumer (distinct from the
# service-side ``process_created`` / ``duplicate_detected`` operations).
_OP_EVENT_REJECTED = "event_rejected"
_OP_EVENT_FAILED = "event_failed"

# ``OnboardingAuditLog.change_summary`` column bound (max_length=500).
_SUMMARY_MAX_LENGTH = 500


def _build_service(session: AsyncSession) -> OnboardingService:
    """Build an :class:`OnboardingService` bound to ``session``.

    Wires the onboarding repositories and the reused employee repository onto
    the supplied session. The service owns the transaction boundary on that
    session (commit/rollback inside ``start_from_event``).

    Args:
        session: The async session the service and its repositories share.

    Returns:
        A fully wired :class:`OnboardingService`.
    """
    return OnboardingService(
        process_repo=OnboardingProcessRepository(session),
        task_repo=OnboardingTaskRepository(session),
        audit_repo=OnboardingAuditRepository(session),
        document_repo=OnboardingDocumentRepository(session),
        contract_repo=OnboardingContractRepository(session),
        employee_repo=EmployeeRepository(session),
        employee_document_repo=DocumentRepository(session),
        employee_contract_repo=ContractRepository(session),
        session=session,
    )


# ---------------------------------------------------------------------------
# FastAPI dependency provider
# ---------------------------------------------------------------------------


async def get_onboarding_service(
    session: AsyncSession = Depends(get_db_session),
) -> OnboardingService:
    """Provide an :class:`OnboardingService` bound to the request session.

    FastAPI ``Depends`` provider used by the onboarding router
    (``api/router.py``) to obtain a service wired onto the shared request-scoped
    async session from the identity module's ``get_db_session``. It assembles
    the onboarding repositories plus the reused
    :class:`~src.modules.employee.infrastructure.employee_repository.EmployeeRepository`
    via :func:`_build_service`; the service owns the transaction boundary on
    that session (commit/rollback inside ``complete_task``).

    This is the single onboarding-service provider for the HTTP layer. The
    onboarding router and error handlers are registered with the main app in
    ``src/main.py``; this provider is the stable entry point they build on
    rather than redefining it.

    Args:
        session: The async database session injected from
            :func:`~src.modules.identity.container.get_db_session`.

    Returns:
        A fully wired :class:`OnboardingService` for the current request.
    """
    return _build_service(session)


def _resolve_event_id(ctx: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
    """Resolve the originating event identifier recorded on audit entries.

    Prefers ARQ's ``ctx["job_id"]`` because it is stable across retries of the
    same job (so every redelivery of one event shares one id). Falls back to an
    ``event_id`` / ``id`` field carried in the payload, and finally generates a
    UUID so an audit entry is always attributable to some identifier.

    Args:
        ctx: The ARQ job context.
        payload: The raw event payload.

    Returns:
        A non-empty string event identifier.
    """
    job_id = ctx.get("job_id")
    if job_id:
        return str(job_id)
    for key in ("event_id", "id"):
        value = payload.get(key)
        if value:
            return str(value)
    return str(uuid4())


def _try_parse_candidate_id(value: Any) -> UUID | None:
    """Best-effort parse of ``candidate_id`` for the rejection audit entry.

    A malformed event may carry a missing, empty, or non-UUID ``candidate_id``.
    The rejection audit records the candidate id only when it is parseable,
    otherwise ``None`` (R1.6's "including its originating ``candidate_id``" is
    satisfied when one is recoverable).

    Args:
        value: The raw ``candidate_id`` value from the payload.

    Returns:
        The parsed :class:`~uuid.UUID`, or ``None`` when it cannot be parsed.
    """
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text:
            try:
                return UUID(text)
            except ValueError:
                return None
    return None


def _truncate_summary(text: str) -> str:
    """Clamp an audit ``change_summary`` to the column's max length.

    Args:
        text: The candidate summary text.

    Returns:
        ``text`` truncated to at most ``_SUMMARY_MAX_LENGTH`` characters.
    """
    return text[:_SUMMARY_MAX_LENGTH]


async def _record_rejection(
    session_maker: async_sessionmaker[AsyncSession],
    payload: Mapping[str, Any],
    event_id: str,
    error: InvalidEventPayloadError,
) -> None:
    """Write a rejection audit entry for a malformed event in its own transaction.

    Opens a fresh session and commits a single ``event_rejected`` audit entry
    (``success = False``) recording the parseable ``candidate_id`` (if any), the
    event id, and the validation reason. The service is never invoked (R1.6,
    R2.6). A failure to write this mandatory audit propagates so the job is
    retried until the rejection can be recorded (the service is still never
    called on retry, since the payload remains malformed).

    Args:
        session_maker: The worker-provided async session factory.
        payload: The raw (malformed) event payload.
        event_id: The resolved originating event identifier.
        error: The validation error explaining why the event was rejected.
    """
    entry = OnboardingAuditLog(
        operation_type=_OP_EVENT_REJECTED,
        entity_type="event",
        candidate_id=_try_parse_candidate_id(payload.get("candidate_id")),
        event_id=event_id,
        success=False,
        change_summary=_truncate_summary(
            f"Rejected malformed candidate_accepted event {event_id}: {error.message}"
        ),
    )
    async with session_maker() as session:
        audit_repo = OnboardingAuditRepository(session)
        await audit_repo.append(entry)
        await session.commit()


async def _record_failure(
    session_maker: async_sessionmaker[AsyncSession],
    validated: ValidatedEventPayload,
    event_id: str,
    error: BaseException,
) -> None:
    """Best-effort write of a failure audit entry after retries are exhausted.

    Opens a fresh session (the service already rolled back its own transaction)
    and commits a single ``event_failed`` audit entry (``success = False``)
    recording the candidate id, the event id, and the error. Any error raised
    while recording the failure is swallowed (logged only) so it never masks the
    original processing error, which the caller re-raises (R1.7).

    Args:
        session_maker: The worker-provided async session factory.
        validated: The validated payload of the event that failed to process.
        event_id: The resolved originating event identifier.
        error: The processing error that exhausted the retries.
    """
    entry = OnboardingAuditLog(
        operation_type=_OP_EVENT_FAILED,
        entity_type="event",
        candidate_id=validated.candidate_id,
        event_id=event_id,
        success=False,
        change_summary=_truncate_summary(
            f"Onboarding failed after exhausting retries for candidate "
            f"{validated.candidate_id} (event {event_id}): {error}"
        ),
    )
    try:
        async with session_maker() as session:
            audit_repo = OnboardingAuditRepository(session)
            await audit_repo.append(entry)
            await session.commit()
    except Exception:
        logger.exception(
            "Failed to record failure audit for candidate %s (event %s)",
            validated.candidate_id,
            event_id,
        )


async def process_candidate_accepted(ctx: dict[str, Any], payload: dict[str, Any]) -> None:
    """ARQ task: consume a ``candidate_accepted`` event and start onboarding.

    Validates the payload, rejecting malformed events with a rejection audit
    entry and no service call (R1.6, R2.6); otherwise builds an
    :class:`OnboardingService` from the worker-provided ``session_maker`` and
    calls :meth:`OnboardingService.start_from_event`, which creates (idempotently
    per ``candidate_id``) the inactive Employee, the OnboardingProcess, the fixed
    checklist, and the creation audit entry in one transaction (R1.1, R1.5).

    Transient errors propagate so ARQ retries the job up to ``max_tries`` (= 3,
    R1.7). On the final attempt the consumer records a failure audit entry before
    re-raising so the failure is recorded (R1.5) and remains visible to ARQ.

    Args:
        ctx: The ARQ job context. Must contain ``session_maker`` (set by the
            worker startup hook); ``job_id`` and ``job_try`` are provided by ARQ
            and used for the event id and final-attempt detection respectively.
        payload: The raw event payload carrying ``candidate_id``, ``name`` (the
            Employee ``full_name``), and ``email``.

    Raises:
        Exception: Re-raises any processing error so ARQ retries the job (or
            marks it failed on the final attempt).
    """
    session_maker: async_sessionmaker[AsyncSession] = ctx["session_maker"]
    event_id = _resolve_event_id(ctx, payload)

    # Step 1: validate. A malformed event is rejected and audited, never
    # invoking the service, and is not retried (R1.6, R2.6).
    try:
        validated = validate_event_payload(payload)
    except InvalidEventPayloadError as exc:
        logger.warning("Rejecting malformed candidate_accepted event %s: %s", event_id, exc.message)
        await _record_rejection(session_maker, payload, event_id, exc)
        return

    # Step 2: process the valid event. start_from_event owns its transaction and
    # rolls back on any failure so nothing partial persists (R1.5).
    try:
        async with session_maker() as session:
            service = _build_service(session)
            await service.start_from_event(
                candidate_id=validated.candidate_id,
                full_name=validated.full_name,
                email=validated.email,
                event_id=event_id,
            )
    except Exception as exc:
        # Transient failure — let ARQ retry. Record the failure only once the
        # retries are exhausted, then re-raise (R1.7).
        job_try = int(ctx.get("job_try") or 1)
        max_tries = int(ctx.get("max_tries") or _MAX_TRIES)
        if job_try >= max_tries:
            logger.error(
                "Onboarding failed after %d/%d attempts for candidate %s (event %s)",
                job_try,
                max_tries,
                validated.candidate_id,
                event_id,
            )
            await _record_failure(session_maker, validated, event_id, exc)
        else:
            logger.warning(
                "Onboarding attempt %d/%d failed for candidate %s (event %s); will retry",
                job_try,
                max_tries,
                validated.candidate_id,
                event_id,
            )
        raise

    logger.info(
        "Processed candidate_accepted event %s for candidate %s",
        event_id,
        validated.candidate_id,
    )


def get_arq_tasks() -> list[Callable[..., Awaitable[Any]]]:
    """Return the ARQ task functions registered by the onboarding module.

    Consumed by the onboarding worker settings (task 12.2) to register the
    consumer with the ARQ worker.

    Returns:
        A list containing :func:`process_candidate_accepted`.
    """
    return [process_candidate_accepted]
