from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from sqlmodel import Session

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

_engine: Engine | None = None


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine

        from src.modules.identity.infrastructure.config import AuthSettings

        settings = AuthSettings()
        url = settings.database_url
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("+asyncpg", "", 1)
        _engine = create_engine(url, echo=False)
    return _engine


def get_session() -> Generator[Session, None, None]:
    with Session(_get_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
