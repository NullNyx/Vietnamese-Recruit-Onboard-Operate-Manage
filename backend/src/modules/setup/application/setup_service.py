"""SetupService — orchestrates the initial setup wizard flow."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.identity.application.password_service import PasswordService
from src.modules.identity.domain.entities import User, UserRole
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils
from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)
from src.modules.setup.domain.entities import SetupState


class SetupAlreadyCompleteError(Exception):
    """Raised when trying to perform setup action after setup is done."""


class SetupService:
    """Orchestrates the single-use initial setup wizard.

    All methods raise ``SetupAlreadyCompleteError`` if setup has already
    been completed (``setup_state.completed_at`` is non-NULL).
    """

    def __init__(self, session: AsyncSession, crypto_utils: CryptoUtils | None = None) -> None:
        self._session = session
        self._crypto = crypto_utils

    async def get_status(self) -> dict:
        """Return current setup status booleans."""
        state = await self._get_state()
        completed = state is not None and state.completed_at is not None

        admin_stmt = select(User).where(User.role == UserRole.SUPER_ADMIN).limit(1)
        admin_exists = (await self._session.execute(admin_stmt)).scalars().first() is not None

        org_configured = state is not None and bool(state.org_name)
        ai_configured = state is not None and bool(state.ai_provider)

        return {
            "setup_complete": completed,
            "admin_exists": admin_exists,
            "org_configured": org_configured,
            "ai_provider_configured": ai_configured,
        }

    async def create_first_admin(self, email: str, password: str, name: str) -> User:
        """Create the initial SUPER_ADMIN user. Idempotent if already done."""
        state = await self._get_state()
        if state is not None and state.completed_at is not None:
            raise SetupAlreadyCompleteError("Setup already completed")

        admin_stmt = select(User).where(User.role == UserRole.SUPER_ADMIN).limit(1)
        existing_admin = (await self._session.execute(admin_stmt)).scalars().first()
        if existing_admin is not None:
            raise SetupAlreadyCompleteError("First administrator already exists")

        existing = (await self._session.execute(
            select(User).where(User.email == email.lower()).limit(1)
        )).scalars().first()
        if existing is not None:
            return existing

        password_hash = PasswordService.hash_password(password)
        user = User(
            email=email.lower(),
            name=name,
            password_hash=password_hash,
            google_sub=f"setup:{uuid4().hex}",
            role=UserRole.SUPER_ADMIN,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def configure_organization(
        self, name: str, tax_code: str, timezone: str
    ) -> None:
        """Save company info to SetupState + sync timezone to OrganizationSettings."""
        state = await self._get_state()
        if state is not None and state.completed_at is not None:
            raise SetupAlreadyCompleteError("Setup already completed")

        if state is None:
            state = SetupState()
            self._session.add(state)

        state.org_name = name
        state.org_tax_code = tax_code
        state.org_timezone = timezone

        # Sync timezone to existing OrganizationSettings (avoids duplication)
        org_repo = OrganizationSettingsRepository(self._session)
        await org_repo.set_timezone(timezone)

        await self._session.flush()

    async def configure_ai_provider(self, provider: str, api_key: str | None) -> None:
        """Save AI provider config. Encrypts API key when a key is provided."""
        state = await self._get_state()
        if state is not None and state.completed_at is not None:
            raise SetupAlreadyCompleteError("Setup already completed")

        if state is None:
            state = SetupState()
            self._session.add(state)

        state.ai_provider = provider
        if api_key and self._crypto:
            state.ai_api_key_enc = self._crypto.encrypt(api_key)
        elif api_key:
            state.ai_api_key_enc = api_key  # plaintext when crypto not available
        else:
            state.ai_api_key_enc = None

        await self._session.flush()

    async def complete_setup(self) -> None:
        """Mark setup as finished. Idempotent."""
        admin_stmt = select(User).where(User.role == UserRole.SUPER_ADMIN).limit(1)
        first_admin = (await self._session.execute(admin_stmt)).scalars().first()
        if first_admin is None:
            raise SetupAlreadyCompleteError("First administrator must be created first")

        state = await self._get_state()
        if state is None:
            state = SetupState()
            self._session.add(state)
        if state.completed_at is None:
            state.completed_at = datetime.now(UTC)
        state.completed_by_user_id = first_admin.id
        await self._session.flush()

    async def _get_state(self) -> SetupState | None:
        stmt = select(SetupState).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()
