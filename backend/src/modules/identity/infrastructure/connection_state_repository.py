"""Repository for singleton Organization Google connection state."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.identity.domain.entities import OrganizationGoogleConnection

VALID_CONNECTION_STATUSES = frozenset(
    {"disconnected", "connected", "degraded", "reauthorization_required"}
)


class OrganizationGoogleConnectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_singleton(self) -> OrganizationGoogleConnection | None:
        result = await self.session.execute(select(OrganizationGoogleConnection).limit(1))
        return result.scalars().first()

    async def upsert_singleton(
        self, connection: OrganizationGoogleConnection
    ) -> OrganizationGoogleConnection:
        existing = await self.get_singleton()
        connection.updated_at = datetime.now(UTC)
        if existing is None:
            self.session.add(connection)
            await self.session.flush()
            return connection
        for field in (
            "status",
            "email",
            "google_sub",
            "email_domain",
            "selected_calendar_id",
            "credential_format_version",
            "credential_key_version",
            "access_token_enc",
            "refresh_token_enc",
            "client_secret_enc",
            "oauth_state_hash",
            "oauth_state_nonce",
            "oauth_state_session_id",
            "oauth_state_expires_at",
            "token_expires_at",
            "connected_by_user_id",
            "updated_at",
        ):
            setattr(existing, field, getattr(connection, field))
        self.session.add(existing)
        await self.session.flush()
        return existing

    async def consume_oauth_state(
        self, state_hash: str, *, now: datetime | None = None
    ) -> OrganizationGoogleConnection | None:
        """Atomically consume an OAuth state stored on the singleton.

        The row lock makes the one-time state invariant hold across workers;
        a replay sees no matching state after the first transaction consumes it.
        """
        current_time = now or datetime.now(UTC)
        state_expires_at = OrganizationGoogleConnection.oauth_state_expires_at
        result = await self.session.execute(
            select(OrganizationGoogleConnection)
            .where(
                OrganizationGoogleConnection.oauth_state_hash == state_hash,
                state_expires_at > current_time,  # type: ignore[operator]
            )
            .with_for_update()
        )
        connection = result.scalars().first()
        if connection is None:
            return None
        connection.oauth_state_hash = None
        connection.oauth_state_nonce = None
        connection.oauth_state_session_id = None
        connection.oauth_state_expires_at = None
        connection.updated_at = current_time
        self.session.add(connection)
        await self.session.flush()
        return connection

    async def mark_reauthorization_required(self) -> OrganizationGoogleConnection:
        """Clear Organization credentials and require an explicit reconnect."""
        existing = await self.get_singleton()
        if existing is None:
            existing = OrganizationGoogleConnection(status="reauthorization_required")
            self.session.add(existing)
        else:
            existing.status = "reauthorization_required"
            existing.email = None
            existing.google_sub = None
            existing.email_domain = None
            existing.selected_calendar_id = None
            existing.access_token_enc = None
            existing.refresh_token_enc = None
            existing.client_secret_enc = None
            existing.oauth_state_hash = None
            existing.oauth_state_nonce = None
            existing.oauth_state_session_id = None
            existing.oauth_state_expires_at = None
            existing.token_expires_at = None
        existing.updated_at = datetime.now(UTC)
        await self.session.flush()
        return existing

    async def update_status(self, status: str) -> OrganizationGoogleConnection:
        """Update only the status field of the organization connection."""
        if status not in VALID_CONNECTION_STATUSES:
            raise ValueError(f"Unsupported Organization Google Connection status: {status}")
        existing = await self.get_singleton()
        if existing is None:
            existing = OrganizationGoogleConnection(status=status)
            self.session.add(existing)
        else:
            existing.status = status
        existing.updated_at = datetime.now(UTC)
        await self.session.flush()
        return existing

    async def disconnect(self) -> OrganizationGoogleConnection:
        existing = await self.get_singleton()
        if existing is None:
            existing = OrganizationGoogleConnection(status="disconnected")
            self.session.add(existing)
        else:
            existing.status = "disconnected"
            existing.email = None
            existing.google_sub = None
            existing.email_domain = None
            existing.selected_calendar_id = None
            existing.access_token_enc = None
            existing.refresh_token_enc = None
            existing.client_secret_enc = None
            existing.oauth_state_hash = None
            existing.oauth_state_nonce = None
            existing.oauth_state_session_id = None
            existing.oauth_state_expires_at = None
            existing.token_expires_at = None
        existing.updated_at = datetime.now(UTC)
        await self.session.flush()
        return existing
