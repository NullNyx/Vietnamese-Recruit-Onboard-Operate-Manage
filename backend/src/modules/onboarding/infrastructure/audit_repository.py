"""Append-only repository for Onboarding audit logging.

Provides :class:`OnboardingAuditRepository`, which persists
:class:`~src.modules.onboarding.domain.entities.OnboardingAuditLog` entries.

Append-only contract (Requirement 8.4)
--------------------------------------
This repository deliberately exposes **only** :meth:`OnboardingAuditRepository.append`.
There is no ``update``, no ``delete``, and no other mutation method. The
onboarding audit trail is immutable by design: once an entry is written it must
never be modified or removed. Enforcing this at the repository surface (by
simply not providing any mutation entry point) means application code cannot
accidentally alter history, complementing the database-level append-only intent
documented in the Alembic migration.

Transactional, mandatory audit (Requirements 8.1, 8.2)
------------------------------------------------------
Unlike the recruitment module's best-effort ``log_audit`` helper, the onboarding
audit is mandatory and transactional. :meth:`append` adds the entry to the
caller's session and ``flush``es it so that any database error surfaces
immediately, **within the caller's transaction**. It deliberately does **not**
commit: the service or consumer that owns the transaction boundary decides when
to commit. As a result, if the audit write fails, the exception propagates and
the surrounding transaction — including the onboarding state change it was meant
to record — is rolled back, so no state change is ever persisted without its
audit entry.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.onboarding.domain.entities import OnboardingAuditLog


class OnboardingAuditRepository:
    """Persists onboarding audit entries in an append-only, transactional manner.

    The repository owns no transaction of its own. It participates in whatever
    transaction the caller (the ``OnboardingService`` or the ARQ consumer) has
    open on the shared :class:`~sqlalchemy.ext.asyncio.AsyncSession`, so the
    audit write succeeds or fails atomically with the state change it records.

    Only :meth:`append` is exposed; there are intentionally no update or delete
    methods, which makes the audit log append-only at the application layer
    (Requirement 8.4).

    Attributes:
        session: The async database session shared with the caller's transaction.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: An SQLAlchemy ``AsyncSession`` whose transaction this
                repository participates in. The session's transaction boundary
                (commit/rollback) is owned by the caller, never by this
                repository.
        """
        self.session = session

    async def append(self, entry: OnboardingAuditLog) -> OnboardingAuditLog:
        """Append an audit entry within the caller's transaction.

        Adds ``entry`` to the session and flushes it so that any database error
        (constraint violation, connection failure, etc.) is raised here, inside
        the caller's transaction. This method does **not** commit: the caller
        owns the transaction boundary. If the flush fails, the exception
        propagates so the caller's transaction — including the state change this
        entry was recording — rolls back, satisfying the mandatory-audit
        guarantee (R8.2).

        Args:
            entry: A fully constructed :class:`OnboardingAuditLog` to persist.

        Returns:
            The same :class:`OnboardingAuditLog` instance with any
            database-populated fields refreshed after the flush.

        Raises:
            Exception: Propagates any database error from the flush so the
                caller's transaction is rolled back. The repository never
                swallows audit-write failures.
        """
        self.session.add(entry)
        await self.session.flush()
        return entry
