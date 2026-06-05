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
from src.modules.employee.infrastructure.config import EmployeeSettings
from src.modules.employee.infrastructure.minio_client import MinIOClient

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

    # --- Seed demo documents with placeholder files in MinIO ------------------
    employee_settings = EmployeeSettings()
    minio = MinIOClient(employee_settings)

    # Minimal valid PDF placeholder (single blank page)
    placeholder_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n"
        b"0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )

    doc_specs = [
        ("cccd", "CCCD_Nguyen_Xuan.pdf", "CCCD/CMND"),
        ("contract", "Hop_dong_lao_dong.pdf", "Hop dong lao dong"),
        ("degree", "Bang_dai_hoc.pdf", "Bang dai hoc"),
    ]

    docs = []
    for doc_type, file_name, description in doc_specs:
        storage_path = f"employees/{employee.id}/{doc_type}/{file_name}"

        # Upload placeholder blob to MinIO first; only persist DB row on success.
        try:
            await minio.upload_file(storage_path, placeholder_pdf, "application/pdf")
        except Exception:
            logger.warning(
                "Could not upload demo document %s to MinIO — skipping DB record.",
                file_name,
            )
            continue

        doc = EmployeeDocument(
            employee_id=employee.id,
            document_type=doc_type,
            file_name=file_name,
            storage_path=storage_path,
            file_size=len(placeholder_pdf),
            mime_type="application/pdf",
            description=description,
        )
        docs.append(doc)

    if docs:
        session.add_all(docs)
        await session.flush()

    logger.info("Demo seed completed: departments, positions, 1 employee + 3 documents.")
    return True
