"""Setup Service.

Handles the logic for first-run setup initialization, token generation,
and verifying the setup state.
"""

from __future__ import annotations

from typing import Protocol

from src.modules.identity.domain.entities import SystemSetup


class SetupRepository(Protocol):
    """Repository interface for SystemSetup persistence."""

    async def get_setup_record(self) -> SystemSetup | None:
        """Get the single setup record."""
        ...

    async def upsert_setup_record(self, record: SystemSetup) -> SystemSetup:
        """Upsert the setup record."""
        ...


class SetupService:
    """Service for managing system setup state."""

    def __init__(self, setup_repository: SetupRepository) -> None:
        """Initialize with repository."""
        self._setup_repository = setup_repository

    async def is_setup_completed(self) -> bool:
        """Check if the first-run setup has been completed.

        Returns:
            True if completed, False if not completed or uninitialized.
        """
        record = await self._setup_repository.get_setup_record()
        if not record:
            return False
        return record.is_setup_completed

    async def initialize_setup_token(self) -> str:
        """Initialize the setup token if not already completed.

        Returns:
            The plain text setup token.
        """
        import secrets

        record = await self._setup_repository.get_setup_record()
        if record and record.is_setup_completed:
            raise ValueError("Setup is already completed")

        if record and record.setup_token:
            return record.setup_token

        token = f"VROOM-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        if not record:
            from uuid import uuid4
            from datetime import datetime, UTC
            record = SystemSetup(
                id=uuid4(),
                is_setup_completed=False,
                setup_token=token,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        else:
            record.setup_token = token

        await self._setup_repository.upsert_setup_record(record)
        return token

    async def verify_setup_token(self, token: str) -> bool:
        """Verify the provided setup token against the DB.

        Args:
            token: The token string provided by the user.

        Returns:
            True if the token is valid, False otherwise.
        """
        record = await self._setup_repository.get_setup_record()
        if not record or record.is_setup_completed or not record.setup_token:
            return False

        import secrets
        return secrets.compare_digest(record.setup_token, token)

    async def lock_setup(self) -> None:
        """Lock the setup by marking it complete and destroying the token.

        Raises:
            ValueError: If setup was never initialized.
        """
        record = await self._setup_repository.get_setup_record()
        if not record:
            raise ValueError("Cannot lock an uninitialized setup")
        
        if record.is_setup_completed:
            return

        record.is_setup_completed = True
        record.setup_token = None
        await self._setup_repository.upsert_setup_record(record)
