"""Minimal bootstrap seed for local development.

Creates departments, positions, and one demo employee linked to
the configured super admin email so ESS can be tested immediately.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from src.modules.employee.domain.entities import Department, Employee, EmployeeDocument, Position

logger = logging.getLogger(__name__)

DEFAULT_DEMO_SUPER_ADMIN_EMAIL = "admin@vroom.local"


async def _count_rows(session: AsyncSession, model: type[SQLModel]) -> int:
    statement = select(func.count()).select_from(model)
    result = await session.execute(statement)
    return int(result.scalar_one())


async def _has_existing_data(session: AsyncSession) -> bool:
    for model in (Department, Position, Employee):
        if await _count_rows(session, model) > 0:
            return True
    return False


async def seed_demo_data(session: AsyncSession) -> bool:
    """Seed minimal data: departments, positions, and one demo employee."""
    from src.modules.identity.infrastructure.config import AuthSettings

    settings = AuthSettings()
    if not settings.auto_seed_sample_data:
        logger.info("Demo seed disabled by config.")
        return False

    if await _has_existing_data(session):
        logger.info("Demo seed skipped: existing data found.")
        return False

    departments = [
        Department(name="Engineering", description="San pham va ky thuat"),
        Department(name="People Operations", description="Van hanh nhan su hang ngay"),
    ]
    session.add_all(departments)
    await session.flush()

    positions = [
        Position(name="Backend Engineer", department_id=departments[0].id),
        Position(name="HR Generalist", department_id=departments[1].id),
    ]
    session.add_all(positions)
    await session.flush()

    employee = Employee(
        employee_code="NV-001",
        full_name="Hoang Xuan Nguyen",
        email="hoangxuannguyen2005@gmail.com",
        phone="0901000001",
        date_of_birth=date(2000, 1, 1),
        gender="male",
        address="123 Le Loi, Quan 1, TP.HCM",
        department_id=departments[1].id,
        position_id=positions[1].id,
        start_date=date(2025, 1, 1),
        contract_type="full_time",
        tax_code="0100000001",
        is_active=True,
    )
    session.add(employee)
    await session.flush()

    docs = [
        EmployeeDocument(
            employee_id=employee.id,
            document_type="cccd",
            file_name="CCCD_Nguyen_Xuan.pdf",
            storage_path=f"employees/{employee.id}/cccd/CCCD_Nguyen_Xuan.pdf",
            file_size=245000,
            mime_type="application/pdf",
            description="CCCD/CMND",
        ),
        EmployeeDocument(
            employee_id=employee.id,
            document_type="contract",
            file_name="Hop_dong_lao_dong.pdf",
            storage_path=f"employees/{employee.id}/contract/Hop_dong_lao_dong.pdf",
            file_size=520000,
            mime_type="application/pdf",
            description="Hop dong lao dong",
        ),
        EmployeeDocument(
            employee_id=employee.id,
            document_type="degree",
            file_name="Bang_dai_hoc.pdf",
            storage_path=f"employees/{employee.id}/degree/Bang_dai_hoc.pdf",
            file_size=380000,
            mime_type="application/pdf",
            description="Bang dai hoc",
        ),
    ]
    session.add_all(docs)
    await session.flush()

    logger.info("Demo seed completed: departments, positions, 1 employee + 3 documents.")
    return True
