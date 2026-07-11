"""Repository for OutboundEmail persistence.

Provides CRUD operations for the outbound_emails table including
idempotency key lookup, status-based queries, and paginated listing.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import asc, col, desc

from src.modules.gmail.domain.entities import OutboundEmail

logger = logging.getLogger(__name__)


class OutboundEmailRepository:
    """Persistence layer for OutboundEmail records.

    Args:
        session: The async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: OutboundEmail) -> OutboundEmail:
        """Persist a new OutboundEmail record.

        Args:
            entity: The OutboundEmail entity to persist.

        Returns:
            The persisted OutboundEmail with generated fields populated.
        """
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def get_by_id(self, outbound_id: UUID) -> OutboundEmail | None:
        """Retrieve an OutboundEmail by its primary key.

        Args:
            outbound_id: The UUID of the outbound email record.

        Returns:
            The OutboundEmail entity, or None if not found.
        """
        stmt = select(OutboundEmail).where(col(OutboundEmail.id) == outbound_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> OutboundEmail | None:
        """Retrieve an OutboundEmail by its idempotency key.

        Args:
            key: The idempotency key string.

        Returns:
            The OutboundEmail entity, or None if not found.
        """
        stmt = select(OutboundEmail).where(col(OutboundEmail.idempotency_key) == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_candidate(
        self,
        candidate_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[OutboundEmail], int]:
        """List OutboundEmail records for a specific candidate.

        Args:
            candidate_id: The UUID of the candidate.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Tuple of (list of OutboundEmail entities, total count).
        """
        base = select(OutboundEmail).where(col(OutboundEmail.candidate_id) == candidate_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        query = base.order_by(desc(col(OutboundEmail.created_at))).offset(offset).limit(page_size)
        result = await self._session.execute(query)

        return list(result.scalars().all()), total

    async def list_by_status(self, status: str, limit: int = 50) -> list[OutboundEmail]:
        """List OutboundEmail records by status, oldest first.

        Args:
            status: The status to filter by (e.g. 'pending', 'failed').
            limit: Maximum number of records to return.

        Returns:
            List of OutboundEmail entities matching the status.
        """
        if not status:
            stmt = select(OutboundEmail).order_by(asc(col(OutboundEmail.created_at))).limit(limit)
        else:
            stmt = (
                select(OutboundEmail)
                .where(col(OutboundEmail.status) == status)
                .order_by(asc(col(OutboundEmail.created_at)))
                .limit(limit)
            )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        outbound_id: UUID,
        status: str,
        *,
        gmail_message_id: str | None = None,
        gmail_thread_id: str | None = None,
        error_message: str | None = None,
        retry_count: int | None = None,
        sender_email: str | None = None,
    ) -> OutboundEmail | None:
        """Update the status and optional result fields of an outbound email.

        Args:
            outbound_id: The UUID of the outbound email.
            status: The new status value.
            gmail_message_id: Optional Gmail message ID on success.
            gmail_thread_id: Optional Gmail thread ID on success.
            error_message: Optional error message on failure.
            retry_count: Optional updated retry count.
            sender_email: Optional sender email from the organization connection.

        Returns:
            The updated OutboundEmail entity, or None if not found.
        """
        values: dict[str, object] = {
            "status": status,
            "updated_at": func.now(),
        }
        if gmail_message_id is not None:
            values["gmail_message_id"] = gmail_message_id
        if gmail_thread_id is not None:
            values["gmail_thread_id"] = gmail_thread_id
        if error_message is not None:
            values["error_message"] = error_message
        if retry_count is not None:
            values["retry_count"] = retry_count
        if sender_email is not None:
            values["sender_email"] = sender_email

        stmt = update(OutboundEmail).where(col(OutboundEmail.id) == outbound_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()

        return await self.get_by_id(outbound_id)
