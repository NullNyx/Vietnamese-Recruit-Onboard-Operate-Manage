"""Bootstrap seed for local development.

Creates departments, positions, and one demo employee linked to
the configured super admin email so ESS can be tested immediately,
plus demo attendance records for active employees.
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

    settings = AuthSettings()  # type: ignore[call-arg]
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


async def seed_demo_attendance(session: AsyncSession) -> bool:
    """Seed demo attendance records for active employees.

    Creates Attendance Records for the work week of June 1-5, 2026 (Mon-Fri)
    to demonstrate both completed and incomplete states.  Skips when the
    config flag is off, records already exist, or no active employees are found.
    Inactive employees are intentionally excluded -- attendance is Employee
    Self-Service data.
    """
    from src.modules.identity.infrastructure.config import AuthSettings

    settings = AuthSettings()  # type: ignore[call-arg]
    if not settings.auto_seed_sample_data:
        logger.info("Attendance demo seed disabled by config.")
        return False

    from src.modules.attendance.domain.entities import AttendanceRecord, AttendanceSource

    # Idempotent: skip if attendance records already exist.
    if await _count_rows(session, AttendanceRecord) > 0:
        logger.info("Attendance demo seed skipped: existing records found.")
        return False

    # Only active employees -- Employee Self-Service data.
    statement = select(Employee).where(Employee.is_active.is_(True))  # type: ignore[arg-type]
    result = await session.execute(statement)
    active_employees = list(result.scalars().all())

    if not active_employees:
        logger.info("Attendance demo seed skipped: no active employees.")
        return False

    from datetime import datetime, timezone

    UTC = timezone.utc

    # Demo work week: June 1-5, 2026 (Mon-Fri).
    # Timestamps stored in UTC; work_date is the date in
    # Asia/Ho_Chi_Minh (UTC+7).
    # Day 1-3: completed (check-in + check-out).
    # Day 4:     checked-in only (incomplete).
    # Day 5:     no record (absent -- implicit state).
    week_data: list[tuple[date, datetime, datetime | None]] = [
        (date(2026, 6, 1), datetime(2026, 6, 1, 1, 0, 0, tzinfo=UTC), datetime(2026, 6, 1, 10, 30, 0, tzinfo=UTC)),  # 08:00-17:30 HCM
        (date(2026, 6, 2), datetime(2026, 6, 2, 1, 15, 0, tzinfo=UTC), datetime(2026, 6, 2, 10, 45, 0, tzinfo=UTC)),  # 08:15-17:45 HCM
        (date(2026, 6, 3), datetime(2026, 6, 3, 0, 55, 0, tzinfo=UTC), datetime(2026, 6, 3, 11, 0, 0, tzinfo=UTC)),  # 07:55-18:00 HCM
        (date(2026, 6, 4), datetime(2026, 6, 4, 2, 0, 0, tzinfo=UTC), None),  # 09:00 HCM, no check-out
    ]

    records: list[AttendanceRecord] = []
    for emp in active_employees:
        for work_date, check_in, check_out in week_data:
            record = AttendanceRecord(
                employee_id=emp.id,
                work_date=work_date,
                check_in_at=check_in,
                check_out_at=check_out,
                check_in_ip="192.168.1.100",
                check_out_ip="192.168.1.100" if check_out else None,
                check_in_user_agent="VroomHR-Demo/1.0",
                check_out_user_agent="VroomHR-Demo/1.0" if check_out else None,
                source=AttendanceSource.WEB,
            )
            records.append(record)

    session.add_all(records)
    await session.flush()

    logger.info(
        "Attendance demo seed completed: %d records for %d active employee(s).",
        len(records),
        len(active_employees),
    )
    return True
