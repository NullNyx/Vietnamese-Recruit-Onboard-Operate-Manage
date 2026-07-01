"""Dependency injection for the Setup module."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.container import get_crypto_utils, get_db_session
from src.modules.setup.application.setup_service import SetupService


async def get_setup_service(
    session: AsyncSession = Depends(get_db_session),
) -> SetupService:
    """Provide SetupService with DB session and crypto helper."""
    return SetupService(session=session, crypto_utils=get_crypto_utils())
