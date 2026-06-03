"""Seed a compact demo dataset for local HR development runs.

Usage:
    cd backend
    python -m scripts.seed_demo_data
"""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.bootstrap.demo_data import seed_demo_data
from src.modules.identity.infrastructure.config import AuthSettings


async def main() -> None:
    settings = AuthSettings()  # type: ignore[call-arg]
    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        seeded = await seed_demo_data(session)
        if seeded:
            await session.commit()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
