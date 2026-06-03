"""Dev sample data bootstrap for the HR modules.

Seeds a compact, realistic dataset for local Docker runs so the HR dashboard,
Recruitment, Gmail, Employees, and Onboarding screens are not empty on first
launch. The seed is intentionally conservative: it only runs when the core demo
tables are empty and the feature flag is enabled.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from src.modules.employee.domain.entities import Department, Employee, Position
from src.modules.employee.infrastructure.employee_repository import EmployeeRepository
from src.modules.gmail.domain.entities import EmailAttachment, EmailMessage, GmailLabelMapping
from src.modules.identity.application.role_service import RoleService
from src.modules.identity.domain.entities import OAuthGrant, User, UserRole
from src.modules.identity.infrastructure.config import AuthSettings
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils
from src.modules.onboarding.container import _build_service
from src.modules.recruitment.domain.entities import Candidate, CVDocument
from src.modules.recruitment.domain.enums import CandidateStatus

logger = logging.getLogger(__name__)

DEFAULT_DEMO_SUPER_ADMIN_EMAIL = "admin@vroom.local"


@dataclass(frozen=True)
class DemoCandidateSpec:
    name: str
    email: str
    status: CandidateStatus
    phone: str
    skills: list[str]
    summary: str


async def _count_rows(session: AsyncSession, model: type[SQLModel]) -> int:
    statement = select(func.count()).select_from(model)
    result = await session.execute(statement)
    return int(result.scalar_one())


async def _has_existing_demo_data(session: AsyncSession) -> bool:
    for model in (
        Department,
        Position,
        Employee,
        Candidate,
        CVDocument,
        EmailMessage,
        OAuthGrant,
    ):
        if await _count_rows(session, model) > 0:
            return True
    return False


async def _get_or_create_admin_user(session: AsyncSession, settings: AuthSettings) -> User:
    admin_email = settings.super_admin_email or DEFAULT_DEMO_SUPER_ADMIN_EMAIL
    role_service = RoleService(session=session, super_admin_email=admin_email)

    await role_service.ensure_super_admin(admin_email)

    statement = select(User).where(func.lower(User.email) == admin_email.lower())
    result = await session.execute(statement)
    admin_user = result.scalars().first()
    if admin_user is not None:
        return admin_user

    statement = select(User).where(User.role == UserRole.ADMIN).order_by(User.created_at)
    result = await session.execute(statement)
    admin_user = result.scalars().first()
    if admin_user is not None:
        return admin_user

    admin_user = User(
        email=admin_email,
        name="Vroom HR Admin",
        google_sub=f"demo-{uuid4()}",
        role=UserRole.ADMIN,
    )
    session.add(admin_user)
    await session.flush()
    return admin_user


async def _seed_departments(session: AsyncSession) -> dict[str, Department]:
    rows = [
        Department(name="Talent Acquisition", description="Tuyển dụng và đầu vào nhân sự"),
        Department(name="People Operations", description="Vận hành nhân sự hằng ngày"),
        Department(name="Engineering", description="Sản phẩm và kỹ thuật"),
    ]
    session.add_all(rows)
    await session.flush()
    return {row.name: row for row in rows}


async def _seed_positions(
    session: AsyncSession, departments: dict[str, Department]
) -> dict[str, Position]:
    rows = [
        Position(name="Recruitment Specialist", department_id=departments["Talent Acquisition"].id),
        Position(name="HR Generalist", department_id=departments["People Operations"].id),
        Position(name="Backend Engineer", department_id=departments["Engineering"].id),
        Position(name="Frontend Engineer", department_id=departments["Engineering"].id),
    ]
    session.add_all(rows)
    await session.flush()
    return {row.name: row for row in rows}


async def _seed_manual_employees(
    session: AsyncSession,
    employee_repo: EmployeeRepository,
    departments: dict[str, Department],
    positions: dict[str, Position],
) -> list[Employee]:
    specs = [
        {
            "full_name": "Nguyen Thi Anh",
            "email": "anh.hr@vroom.local",
            "department_id": departments["People Operations"].id,
            "position_id": positions["HR Generalist"].id,
            "phone": "0901000001",
            "start_date": date(2025, 10, 1),
            "contract_type": "official",
            "tax_code": "0100000001",
        },
        {
            "full_name": "Tran Minh Quan",
            "email": "quan.talent@vroom.local",
            "department_id": departments["Talent Acquisition"].id,
            "position_id": positions["Recruitment Specialist"].id,
            "phone": "0901000002",
            "start_date": date(2025, 11, 15),
            "contract_type": "official",
            "tax_code": "0100000002",
        },
        {
            "full_name": "Le Hoang Phuc",
            "email": "phuc.engineering@vroom.local",
            "department_id": departments["Engineering"].id,
            "position_id": positions["Backend Engineer"].id,
            "phone": "0901000003",
            "start_date": date(2025, 12, 2),
            "contract_type": "official",
            "tax_code": "0100000003",
        },
    ]

    created: list[Employee] = []
    for spec in specs:
        existing = await employee_repo.get_by_email(spec["email"])
        if existing is not None:
            created.append(existing)
            continue

        employee = Employee(
            employee_code=await employee_repo.get_next_code(),
            full_name=spec["full_name"],
            email=spec["email"],
            phone=spec["phone"],
            department_id=spec["department_id"],
            position_id=spec["position_id"],
            start_date=spec["start_date"],
            contract_type=spec["contract_type"],
            tax_code=spec["tax_code"],
            is_active=True,
        )
        session.add(employee)
        await session.flush()
        created.append(employee)

    return created


async def _seed_recruitment_data(session: AsyncSession) -> dict[str, Candidate]:
    specs = [
        DemoCandidateSpec(
            name="Mai Nguyen",
            email="mai.nguyen@example.com",
            status=CandidateStatus.NEW,
            phone="0902000001",
            skills=["Vue", "UI", "Figma"],
            summary="Ung vien frontend moi gui CV.",
        ),
        DemoCandidateSpec(
            name="Do Duc Anh",
            email="duc.anh@example.com",
            status=CandidateStatus.REVIEWING,
            phone="0902000002",
            skills=["Python", "FastAPI", "PostgreSQL"],
            summary="Ung vien backend dang cho HR review CV.",
        ),
        DemoCandidateSpec(
            name="Le Thi Huyen",
            email="huyen.le@example.com",
            status=CandidateStatus.INTERVIEW_SCHEDULED,
            phone="0902000003",
            skills=["Recruitment", "Excel", "Communication"],
            summary="Ung vien da len lich phong van.",
        ),
        DemoCandidateSpec(
            name="Tran Quang Huy",
            email="huy.tran@example.com",
            status=CandidateStatus.REJECTED,
            phone="0902000004",
            skills=["QA", "Automation"],
            summary="Ung vien khong phu hop dot nay.",
        ),
        DemoCandidateSpec(
            name="Pham Hong Nhung",
            email="nhung.pham@example.com",
            status=CandidateStatus.ARCHIVED,
            phone="0902000005",
            skills=["HR", "Onboarding"],
            summary="Ho so cu duoc luu tru.",
        ),
        DemoCandidateSpec(
            name="Nguyen Van Long",
            email="long.nguyen@example.com",
            status=CandidateStatus.ACCEPTED,
            phone="0902000006",
            skills=["Go", "Docker", "Kubernetes"],
            summary="Ung vien da accept va chuyen sang onboarding.",
        ),
        DemoCandidateSpec(
            name="Bui Thu Ha",
            email="ha.bui@example.com",
            status=CandidateStatus.ACCEPTED,
            phone="0902000007",
            skills=["Product", "Operations"],
            summary="Ung vien accept thu hai de demo onboarding complete.",
        ),
    ]

    created: dict[str, Candidate] = {}
    now = datetime.now(UTC)
    for index, spec in enumerate(specs, start=1):
        candidate = Candidate(
            name=spec.name,
            email=spec.email,
            phone=spec.phone,
            skills=spec.skills,
            experience=[{"company": "Vroom Demo", "years": 2}],
            education=[{"school": "Demo University", "degree": "Bachelor"}],
            summary=spec.summary,
            status=spec.status.value,
            confidence_score=0.55 + (index * 0.05),
            created_at=now - timedelta(days=10 - index),
            updated_at=now - timedelta(days=5 - index),
        )

        if spec.status == CandidateStatus.REJECTED:
            candidate.rejection_reason = "Thieu kinh nghiem phu hop"
            candidate.rejected_at = now - timedelta(days=2)
        elif spec.status == CandidateStatus.ARCHIVED:
            candidate.archived_at = now - timedelta(days=1)
        elif spec.status == CandidateStatus.ACCEPTED:
            candidate.accepted_at = now - timedelta(hours=index)

        session.add(candidate)
        await session.flush()
        created[spec.email] = candidate

    return created


async def _seed_gmail_data(session: AsyncSession, admin_user: User, crypto: CryptoUtils) -> None:
    now = datetime.now(UTC)

    grant = OAuthGrant(
        user_id=admin_user.id,
        access_token_enc=crypto.encrypt("demo-access-token"),
        refresh_token_enc=crypto.encrypt("demo-refresh-token"),
        scopes=[
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
        ],
        token_expires_at=now + timedelta(days=7),
        is_valid=True,
    )
    session.add(grant)

    messages = [
        EmailMessage(
            user_id=admin_user.id,
            gmail_message_id="demo-gmail-msg-1",
            gmail_thread_id="demo-gmail-thread-1",
            subject="CV - Do Duc Anh - Backend Engineer",
            sender_email="duc.anh@example.com",
            sender_name="Do Duc Anh",
            recipient_emails=[admin_user.email],
            cc_emails=[],
            received_at=now - timedelta(days=1, hours=2),
            snippet="Attached is my CV for the Backend Engineer role.",
            label_ids=["INBOX", "VroomHR/cv"],
            has_attachments=True,
            category="cv",
        ),
        EmailMessage(
            user_id=admin_user.id,
            gmail_message_id="demo-gmail-msg-2",
            gmail_thread_id="demo-gmail-thread-2",
            subject="CV - Le Thi Huyen - Recruitment Specialist",
            sender_email="huyen.le@example.com",
            sender_name="Le Thi Huyen",
            recipient_emails=[admin_user.email],
            cc_emails=[],
            received_at=now - timedelta(days=1),
            snippet="Looking forward to joining Vroom HR.",
            label_ids=["INBOX", "VroomHR/cv"],
            has_attachments=True,
            category="cv",
        ),
        EmailMessage(
            user_id=admin_user.id,
            gmail_message_id="demo-gmail-msg-3",
            gmail_thread_id="demo-gmail-thread-3",
            subject="Recruitment check-in",
            sender_email="team.lead@example.com",
            sender_name="Team Lead",
            recipient_emails=[admin_user.email],
            cc_emails=[],
            received_at=now - timedelta(hours=12),
            snippet="Please review the candidate shortlist before noon.",
            label_ids=["INBOX", "VroomHR/internal"],
            has_attachments=False,
            category="internal",
        ),
    ]
    session.add_all(messages)
    await session.flush()

    attachments = [
        EmailAttachment(
            email_message_id=messages[0].id,
            gmail_attachment_id="demo-attach-1",
            filename="Do_Duc_Anh_CV.pdf",
            mime_type="application/pdf",
            size_bytes=245_000,
            storage_path="gmail/demo/Do_Duc_Anh_CV.pdf",
        ),
        EmailAttachment(
            email_message_id=messages[1].id,
            gmail_attachment_id="demo-attach-2",
            filename="Le_Thi_Huyen_CV.pdf",
            mime_type="application/pdf",
            size_bytes=198_000,
            storage_path="gmail/demo/Le_Thi_Huyen_CV.pdf",
        ),
    ]
    session.add_all(attachments)

    label_mappings = [
        GmailLabelMapping(
            user_id=admin_user.id,
            label_name="VroomHR/cv",
            gmail_label_id="Label_CV",
            is_initialized=True,
        ),
        GmailLabelMapping(
            user_id=admin_user.id,
            label_name="VroomHR/internal",
            gmail_label_id="Label_Internal",
            is_initialized=True,
        ),
    ]
    session.add_all(label_mappings)
    await session.flush()


async def seed_demo_data(session: AsyncSession) -> bool:
    """Seed a compact, realistic HR demo dataset.

    Returns:
        True when the seed ran, False when it was skipped.
    """

    settings = AuthSettings()  # type: ignore[call-arg]
    if not settings.auto_seed_sample_data:
        logger.info("Demo seed disabled by config.")
        return False

    if await _has_existing_demo_data(session):
        logger.info("Demo seed skipped: existing data found.")
        return False

    if settings.super_admin_email is None:
        logger.info(
            "AUTH_SUPER_ADMIN_EMAIL unset; using demo admin '%s'.",
            DEFAULT_DEMO_SUPER_ADMIN_EMAIL,
        )

    admin_user = await _get_or_create_admin_user(session, settings)

    crypto = CryptoUtils(settings.oauth_token_encryption_key)
    employee_repo = EmployeeRepository(session)
    onboarding_service = _build_service(session)

    departments = await _seed_departments(session)
    positions = await _seed_positions(session, departments)
    await _seed_manual_employees(session, employee_repo, departments, positions)
    candidates = await _seed_recruitment_data(session)
    await _seed_gmail_data(session, admin_user, crypto)

    accepted_candidates = [
        candidates["long.nguyen@example.com"],
        candidates["ha.bui@example.com"],
    ]

    first_process = await onboarding_service.start_from_event(
        candidate_id=accepted_candidates[0].id,
        full_name=accepted_candidates[0].name,
        email=accepted_candidates[0].email,
        event_id="demo-event-onboarding-1",
    )
    first_detail = await onboarding_service.get_process(first_process.id)
    if first_detail.tasks:
        await onboarding_service.complete_task(task_id=first_detail.tasks[0].id, actor=admin_user)

    second_process = await onboarding_service.start_from_event(
        candidate_id=accepted_candidates[1].id,
        full_name=accepted_candidates[1].name,
        email=accepted_candidates[1].email,
        event_id="demo-event-onboarding-2",
    )
    second_detail = await onboarding_service.get_process(second_process.id)
    for task in second_detail.tasks:
        await onboarding_service.complete_task(task_id=task.id, actor=admin_user)

    logger.info("Demo seed completed.")
    return True
