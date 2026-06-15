"""Bootstrap seed for local development.

Creates departments, positions, and one demo employee linked to
the configured super admin email so ESS can be tested immediately,
plus demo attendance records for active employees.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo

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

    Creates Attendance Records for the current work week (Mon-Thu)
    to demonstrate both completed and incomplete states.  Skips when the
    config flag is off, records already exist for the target week, or no
    active employees are found.  Inactive employees are intentionally
    excluded -- attendance is Employee Self-Service data.
    """
    from src.modules.identity.infrastructure.config import AuthSettings

    settings = AuthSettings()  # type: ignore[call-arg]
    if not settings.auto_seed_sample_data:
        logger.info("Attendance demo seed disabled by config.")
        return False

    from datetime import UTC, datetime

    from src.modules.attendance.domain.entities import AttendanceRecord, AttendanceSource

    # Only active employees -- Employee Self-Service data.
    statement = select(Employee).where(Employee.is_active.is_(True))  # type: ignore[arg-type]
    result = await session.execute(statement)
    active_employees = list(result.scalars().all())

    if not active_employees:
        logger.info("Attendance demo seed skipped: no active employees.")
        return False

    # Compute dynamic work week: Monday of current week + 4 days.
    # All seed dates must be in the past or present (not future).
    today = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    monday = today - timedelta(days=today.weekday())
    # Shift back one week if Thursday of current week is still ahead.
    if monday + timedelta(days=3) > today:
        monday -= timedelta(days=7)

    # Idempotent: skip if records already exist for these employees + dates.
    emp_ids = [emp.id for emp in active_employees]
    week_end = monday + timedelta(days=4)
    count_stmt = (
        select(func.count())
        .select_from(AttendanceRecord)
        .where(
            AttendanceRecord.employee_id.in_(emp_ids),  # type: ignore[arg-type]
            AttendanceRecord.work_date.between(monday, week_end),
        )
    )
    count_result = await session.execute(count_stmt)
    if count_result.scalar_one() > 0:
        logger.info("Attendance demo seed skipped: existing records found for target week.")
        return False

    # Demo work week: Monday - Thursday of current week.
    # Timestamps stored in UTC; work_date is the date in
    # Asia/Ho_Chi_Minh (UTC+7).
    # Day 1-3: completed (check-in + check-out).
    # Day 4:   checked-in only (incomplete).
    # Day 5:   no record (absent -- implicit state).

    def _hcm_utc(d: date, hour: int, minute: int = 0) -> datetime:
        """Convert Asia/Ho_Chi_Minh time (UTC+7) to aware UTC datetime."""
        hcm = ZoneInfo("Asia/Ho_Chi_Minh")
        return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=hcm).astimezone(UTC)

    day1 = monday
    day2 = monday + timedelta(days=1)
    day3 = monday + timedelta(days=2)
    day4 = monday + timedelta(days=3)

    week_data: list[tuple[date, datetime, datetime | None]] = [
        (day1, _hcm_utc(day1, 8, 0), _hcm_utc(day1, 17, 30)),  # 08:00-17:30 HCM
        (day2, _hcm_utc(day2, 8, 15), _hcm_utc(day2, 17, 45)),  # 08:15-17:45 HCM
        (day3, _hcm_utc(day3, 7, 55), _hcm_utc(day3, 18, 0)),  # 07:55-18:00 HCM
        (day4, _hcm_utc(day4, 9, 0), None),  # 09:00 HCM, no check-out
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


async def seed_demo_payslips(session: AsyncSession) -> bool:
    """Seed demo published payslips for active employees.

    Creates 2 published payslips per active employee for the last 2
    completed months. Skips when the config flag is off, payslips
    already exist, or no active employees are found.
    """
    from src.modules.identity.infrastructure.config import AuthSettings

    settings = AuthSettings()  # type: ignore[call-arg]
    if not settings.auto_seed_sample_data:
        logger.info("Payslip demo seed disabled by config.")
        return False

    from datetime import UTC, datetime

    from src.modules.payslip.domain.entities import Payslip

    # Only active employees -- Employee Self-Service data.
    statement = select(Employee).where(Employee.is_active.is_(True))  # type: ignore[arg-type]
    result = await session.execute(statement)
    active_employees = list(result.scalars().all())

    if not active_employees:
        logger.info("Payslip demo seed skipped: no active employees.")
        return False

    # Idempotent: only skip payslips that already exist per (employee_id, period).
    emp_ids = [emp.id for emp in active_employees]
    existing_stmt = select(
        Payslip.employee_id,
        Payslip.pay_period_start,
        Payslip.pay_period_end,
    ).where(Payslip.employee_id.in_(emp_ids))  # type: ignore[arg-type]
    existing_result = await session.execute(existing_stmt)
    existing_periods = {
        (row.employee_id, row.pay_period_start, row.pay_period_end) for row in existing_result
    }

    # Build 2 demo payslips per employee for the last 2 completed months.
    today = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    current_month_start = today.replace(day=1)

    # Compute last 2 completed months.
    payslip_periods: list[tuple[date, date]] = []
    for i in range(1, 3):
        # Go back i months, then get start/end of that month.
        month = current_month_start.month - i
        year = current_month_start.year
        while month < 1:
            month += 12
            year -= 1
        from calendar import monthrange

        _, last_day = monthrange(year, month)
        period_start = date(year, month, 1)
        period_end = date(year, month, last_day)
        payslip_periods.append((period_start, period_end))

    payslips: list[Payslip] = []
    for emp in active_employees:
        for period_start, period_end in payslip_periods:
            # Skip if this (employee, period) already exists
            if (emp.id, period_start, period_end) in existing_periods:
                continue

            # Simple demo amounts
            gross = 15_000_000
            deductions = round(gross * 0.105)  # 10.5% insurance
            net = gross - deductions

            payslip = Payslip(
                employee_id=emp.id,
                pay_period_start=period_start,
                pay_period_end=period_end,
                gross_amount=gross,
                total_deductions=deductions,
                net_amount=net,
                currency="VND",
                details={
                    "bhxh": round(gross * 0.08),
                    "bhyt": round(gross * 0.015),
                    "bhtn": round(gross * 0.01),
                    "work_days": 26,
                    "actual_work_days": 26,
                },
                published=True,
                published_at=datetime.now(UTC),
            )
            payslips.append(payslip)

    session.add_all(payslips)
    await session.flush()

    logger.info(
        "Payslip demo seed completed: %d new payslips for %d active employee(s).",
        len(payslips),
        len(active_employees),
    )
    return True
