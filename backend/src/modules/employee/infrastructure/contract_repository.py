"""Repository for Contract entity CRUD operations."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.employee.domain.contract import Contract


class ContractRepository:
    """Handles Contract persistence using async SQLAlchemy sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, contract: Contract) -> Contract:
        self._session.add(contract)
        await self._session.flush()
        return contract

    async def get_by_id(self, contract_id: UUID) -> Contract | None:
        stmt = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_by_employee(self, employee_id: UUID) -> list[Contract]:
        stmt = (
            select(Contract)
            .where(Contract.employee_id == employee_id)
            .order_by(Contract.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, contract_id: UUID, data: dict[str, Any]) -> Contract | None:
        stmt = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(stmt)
        contract = result.scalars().first()

        if contract is None:
            return None

        for key, value in data.items():
            if hasattr(contract, key):
                setattr(contract, key, value)

        contract.updated_at = datetime.now(UTC)
        self._session.add(contract)
        await self._session.flush()
        return contract

    async def delete(self, contract_id: UUID) -> bool:
        stmt = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(stmt)
        contract = result.scalars().first()

        if contract is None:
            return False

        await self._session.delete(contract)
        await self._session.flush()
        return True
