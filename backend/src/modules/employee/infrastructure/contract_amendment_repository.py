"""Repository for ContractAmendment entity CRUD operations."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.employee.domain.contract_amendment import ContractAmendment


class ContractAmendmentRepository:
    """Handles ContractAmendment persistence using async SQLAlchemy sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, amendment: ContractAmendment) -> ContractAmendment:
        self._session.add(amendment)
        await self._session.flush()
        return amendment

    async def list_by_contract(self, contract_id: UUID) -> list[ContractAmendment]:
        stmt = (
            select(ContractAmendment)
            .where(ContractAmendment.contract_id == contract_id)
            .order_by(ContractAmendment.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, amendment_id: UUID, data: dict[str, Any]) -> ContractAmendment | None:
        stmt = select(ContractAmendment).where(ContractAmendment.id == amendment_id)
        result = await self._session.execute(stmt)
        amendment = result.scalars().first()

        if amendment is None:
            return None

        for key, value in data.items():
            if hasattr(amendment, key):
                setattr(amendment, key, value)

        self._session.add(amendment)
        await self._session.flush()
        return amendment
