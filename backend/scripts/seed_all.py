"""Comprehensive seed script for Vroom HR — Vietnamese-oriented demo data.

Creates 50+ records per domain: departments, positions, employees, users,
job openings, candidates, interviews, attendance, payslips, onboarding,
and employee requests.

Usage:
    cd backend && uv run python scripts/seed_all.py

Requires: Postgres running (docker compose up -d postgres)
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel, select

# Reuse the project's password hashing
from src.modules.identity.infrastructure.password_utils import hash_password
from src.modules.identity.domain.entities import User, UserRole
from src.modules.employee.domain.entities import Department, Employee, Position
from src.modules.gmail.domain.entities import EmailMessage  # noqa: F401 - needed for FK resolution
from src.modules.recruitment.domain.entities import (
    Candidate,
    Interview,
    InterviewParticipant,
    JobOpening,
    OrganizationSettings,
)
from src.modules.attendance.domain.entities import AttendanceRecord, AttendanceSource
from src.modules.payslip.domain.entities import Payslip, PayslipStatus
from src.modules.onboarding.domain.entities import OnboardingProcess, OnboardingTask
from src.modules.employee_request.domain.entities import EmployeeRequest
from src.modules.employee_request.domain.enums import LeaveType, RequestStatus, RequestType

logger = logging.getLogger(__name__)
HCM = ZoneInfo("Asia/Ho_Chi_Minh")

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/vroom_hr"

# ── Vietnamese data pools ──────────────────────────────────────────

FAMILY_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ",
    "Ngô", "Dương", "Lý", "Đinh", "Phan", "Mai", "Hà", "Văn", "Tạ",
    "Trịnh", "Đoàn", "Lương", "Cao", "Tô", "Nghiêm", "Hồ",
]

MALE_MIDDLE = ["Văn", "Đức", "Minh", "Quang", "Anh", "Tuấn", "Thanh", "Hữu", "Xuân", "Hồng"]
FEMALE_MIDDLE = ["Thị", "Minh", "Thanh", "Ngọc", "Mỹ", "Thu", "Kim", "Hồng", "Ánh", "Phương"]

MALE_FIRST = [
    "Anh", "Bảo", "Cường", "Dũng", "Đạt", "Giang", "Hiếu", "Hùng", "Huy",
    "Khang", "Khoa", "Kiên", "Long", "Lâm", "Mạnh", "Nam", "Nghĩa", "Phong",
    "Phúc", "Quân", "Quốc", "Sơn", "Tài", "Thắng", "Thành", "Tuấn", "Trung",
    "Tùng", "Việt", "Vinh",
]
FEMALE_FIRST = [
    "Anh", "Bình", "Châu", "Diệu", "Dung", "Hà", "Hạnh", "Hoa", "Hương",
    "Lan", "Linh", "Ly", "Mai", "Minh", "Ngọc", "Nhi", "Quỳnh", "Thảo",
    "Thúy", "Trang", "Uyên", "Vy", "Xuân", "Yến", "Ánh",
]

STREETS = [
    "Nguyễn Huệ", "Lê Lợi", "Trần Hưng Đạo", "Hai Bà Trưng",
    "Lý Thường Kiệt", "Phạm Ngũ Lão", "Nguyễn Trãi", "Điện Biên Phủ",
    "Võ Văn Kiệt", "Hoàng Diệu", "Bùi Thị Xuân", "Cách Mạng Tháng 8",
]
DISTRICTS = [
    "Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 10",
    "Quận Bình Thạnh", "Quận Tân Bình", "Quận Phú Nhuận",
]
CITIES = ["TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Hải Phòng", "Cần Thơ"]

SKILLS_POOL = [
    "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js",
    "PostgreSQL", "Docker", "Kubernetes", "AWS", "GCP", "Terraform",
    "Go", "Rust", "Java", "Spring Boot", "Kotlin", "Swift",
    "Flutter", "React Native", "Vue.js", "Angular", "GraphQL", "REST API",
    "CI/CD", "Git", "Agile/Scrum", "Linux", "System Design",
    "Excel", "Power BI", "Tableau", "SAP", "QuickBooks",
    "Tuyển dụng IT", "Đào tạo nhân sự", "C&B", "Luật lao động",
    "Bán hàng B2B", "Chăm sóc khách hàng", "Digital Marketing",
    "SEO", "Content Writing", "Figma", "Adobe Suite",
]

# ── Helpers ─────────────────────────────────────────────────────────

def rng() -> random.Random:
    return random.Random()


def vn_phone(r: random.Random) -> str:
    return r.choice(["09", "08", "07", "03"]) + "".join(str(r.randint(0, 9)) for _ in range(8))


def vn_address(r: random.Random) -> str:
    return f"{r.randint(1, 999)} {r.choice(STREETS)}, {r.choice(DISTRICTS)}, {r.choice(CITIES)}"


def make_email(full_name: str) -> str:
    parts = full_name.lower().split()
    if len(parts) >= 2:
        first = parts[-1]
        initials = "".join(p[0] for p in parts[:-1])
        return f"{first}.{initials}@vroom.vn"
    return f"{parts[0]}@vroom.vn"


# ── Seed functions ──────────────────────────────────────────────────

async def seed_organization(session: AsyncSession) -> OrganizationSettings:
    org = OrganizationSettings(
        id=uuid4(),
        name="Công ty TNHH Công Nghệ Vroom Việt Nam",
        timezone="Asia/Ho_Chi_Minh",
        allowed_domains=["vroom.vn"],
    )
    session.add(org)
    await session.flush()
    return org


async def seed_departments(session: AsyncSession) -> dict[str, Department]:
    dept_data = [
        ("Ban Giám Đốc", "Ban lãnh đạo cấp cao"),
        ("Phòng Kỹ Thuật", "Phát triển phần mềm và hạ tầng"),
        ("Phòng Sản Phẩm", "Quản lý và thiết kế sản phẩm"),
        ("Phòng Nhân Sự", "Tuyển dụng, đào tạo và chăm sóc nhân viên"),
        ("Phòng Kinh Doanh", "Kinh doanh và phát triển thị trường"),
        ("Phòng Tài Chính - Kế Toán", "Tài chính, kế toán và kiểm soát"),
    ]
    depts: dict[str, Department] = {}
    for name, desc in dept_data:
        d = Department(id=uuid4(), name=name, description=desc)
        session.add(d)
        depts[name] = d
    await session.flush()
    return depts


async def seed_positions(session: AsyncSession, depts: dict[str, Department]) -> dict[str, Position]:
    pos_data = [
        ("Giám đốc điều hành (CEO)", "Ban Giám Đốc"),
        ("Giám đốc Kỹ thuật (CTO)", "Ban Giám Đốc"),
        ("Giám đốc Tài chính (CFO)", "Ban Giám Đốc"),
        ("Trưởng phòng Kỹ Thuật", "Phòng Kỹ Thuật"),
        ("Senior Backend Developer", "Phòng Kỹ Thuật"),
        ("Senior Frontend Developer", "Phòng Kỹ Thuật"),
        ("Junior Frontend Developer", "Phòng Kỹ Thuật"),
        ("Junior Backend Developer", "Phòng Kỹ Thuật"),
        ("DevOps Engineer", "Phòng Kỹ Thuật"),
        ("QA/Tester", "Phòng Kỹ Thuật"),
        ("Product Manager", "Phòng Sản Phẩm"),
        ("UI/UX Designer", "Phòng Sản Phẩm"),
        ("Business Analyst", "Phòng Sản Phẩm"),
        ("Trưởng phòng Nhân Sự", "Phòng Nhân Sự"),
        ("Chuyên viên Tuyển dụng", "Phòng Nhân Sự"),
        ("Chuyên viên C&B", "Phòng Nhân Sự"),
        ("Trưởng phòng Kinh Doanh", "Phòng Kinh Doanh"),
        ("Nhân viên Kinh Doanh", "Phòng Kinh Doanh"),
        ("Chuyên viên Marketing", "Phòng Kinh Doanh"),
        ("CSKH (Chăm sóc khách hàng)", "Phòng Kinh Doanh"),
        ("Kế toán trưởng", "Phòng Tài Chính - Kế Toán"),
        ("Kế toán viên", "Phòng Tài Chính - Kế Toán"),
        ("Chuyên viên Phân tích Tài chính", "Phòng Tài Chính - Kế Toán"),
        ("Thủ quỹ", "Phòng Tài Chính - Kế Toán"),
    ]
    positions: dict[str, Position] = {}
    for name, dept_name in pos_data:
        p = Position(id=uuid4(), name=name, department_id=depts[dept_name].id)
        session.add(p)
        positions[name] = p
    await session.flush()
    return positions


async def seed_admin_user(session: AsyncSession) -> User:
    admin = User(
        id=uuid4(),
        email="hr@vroom.com",
        name="HR Admin",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    return admin


async def seed_employees(
    session: AsyncSession,
    depts: dict[str, Department],
    positions: dict[str, Position],
    admin: User,
    count: int = 55,
) -> list[Employee]:
    r = rng()

    # Position mapping per department
    dept_positions: dict[str, list[Position]] = {}
    for p in positions.values():
        for dept_name, dept_obj in depts.items():
            if p.department_id == dept_obj.id:
                dept_positions.setdefault(dept_name, []).append(p)

    key_roles: list[dict] = [
        {"name": "Nguyễn Minh Tuấn", "gender": "male", "dept": "Ban Giám Đốc", "pos": "Giám đốc điều hành (CEO)", "dob": date(1978, 5, 12), "start": date(2019, 1, 15)},
        {"name": "Trần Đức Thắng", "gender": "male", "dept": "Ban Giám Đốc", "pos": "Giám đốc Kỹ thuật (CTO)", "dob": date(1980, 8, 22), "start": date(2019, 3, 1)},
        {"name": "Lê Thanh Hà", "gender": "female", "dept": "Ban Giám Đốc", "pos": "Giám đốc Tài chính (CFO)", "dob": date(1982, 12, 5), "start": date(2019, 6, 1)},
        {"name": "Phạm Quang Huy", "gender": "male", "dept": "Phòng Kỹ Thuật", "pos": "Trưởng phòng Kỹ Thuật", "dob": date(1985, 3, 18), "start": date(2020, 2, 1)},
        {"name": "Hoàng Ngọc Linh", "gender": "female", "dept": "Phòng Sản Phẩm", "pos": "Product Manager", "dob": date(1988, 7, 14), "start": date(2020, 5, 1)},
        {"name": "Vũ Thị Hương", "gender": "female", "dept": "Phòng Nhân Sự", "pos": "Trưởng phòng Nhân Sự", "dob": date(1986, 9, 30), "start": date(2020, 8, 1)},
        {"name": "Đặng Văn Nam", "gender": "male", "dept": "Phòng Kinh Doanh", "pos": "Trưởng phòng Kinh Doanh", "dob": date(1984, 11, 8), "start": date(2020, 1, 15)},
        {"name": "Bùi Thanh Mai", "gender": "female", "dept": "Phòng Tài Chính - Kế Toán", "pos": "Kế toán trưởng", "dob": date(1983, 4, 25), "start": date(2020, 4, 1)},
    ]

    employees: list[Employee] = []
    used_emails: set[str] = set()
    used_names: set[str] = set()
    emp_counter = 1

    def create_employee(name: str, gender: str, dept_name: str, pos_name: str,
                        dob: date, start: date, is_active: bool = True) -> Employee:
        nonlocal emp_counter
        email = make_email(name)
        base_email = email
        attempt = 0
        while email in used_emails:
            attempt += 1
            local, domain = base_email.split("@")
            email = f"{local}{attempt}@{domain}"
        used_emails.add(email)
        used_names.add(name)

        emp = Employee(
            id=uuid4(),
            employee_code=f"NV-{emp_counter:03d}",
            full_name=name,
            email=email,
            phone=vn_phone(r),
            date_of_birth=dob,
            gender=gender,
            address=vn_address(r),
            department_id=depts[dept_name].id,
            position_id=positions[pos_name].id,
            start_date=start,
            contract_type="full_time",
            tax_code=f"{r.randint(1000000000, 9999999999)}",
            is_active=is_active,
        )
        emp_counter += 1
        return emp

    # Create key employees
    key_employees: dict[str, Employee] = {}
    for kr in key_roles:
        emp = create_employee(kr["name"], kr["gender"], kr["dept"], kr["pos"], kr["dob"], kr["start"])
        key_employees[kr["name"]] = emp
        employees.append(emp)
        session.add(emp)

    # Manager hierarchy
    ceo = key_employees["Nguyễn Minh Tuấn"]
    for kr_name in ["Trần Đức Thắng", "Lê Thanh Hà", "Phạm Quang Huy", "Hoàng Ngọc Linh",
                     "Vũ Thị Hương", "Đặng Văn Nam", "Bùi Thanh Mai"]:
        key_employees[kr_name].manager_id = ceo.id

    def get_dept_manager(dept_name: str) -> Employee | None:
        manager_map = {
            "Ban Giám Đốc": key_employees.get("Nguyễn Minh Tuấn"),
            "Phòng Kỹ Thuật": key_employees.get("Phạm Quang Huy"),
            "Phòng Sản Phẩm": key_employees.get("Hoàng Ngọc Linh"),
            "Phòng Nhân Sự": key_employees.get("Vũ Thị Hương"),
            "Phòng Kinh Doanh": key_employees.get("Đặng Văn Nam"),
            "Phòng Tài Chính - Kế Toán": key_employees.get("Bùi Thanh Mai"),
        }
        return manager_map.get(dept_name)

    # Regular employees
    remaining = count - len(key_roles)
    inactive_indices = set(r.sample(range(remaining), 3))

    dept_weight_map = {
        "Ban Giám Đốc": 0,
        "Phòng Kỹ Thuật": 14,
        "Phòng Sản Phẩm": 8,
        "Phòng Nhân Sự": 6,
        "Phòng Kinh Doanh": 16,
        "Phòng Tài Chính - Kế Toán": 8,
    }
    dept_names_list = list(dept_weight_map.keys())
    dept_weights = list(dept_weight_map.values())

    for i in range(remaining):
        is_female = r.random() < 0.45
        gender = "female" if is_female else "male"
        family = r.choice(FAMILY_NAMES)
        middle = r.choice(FEMALE_MIDDLE if is_female else MALE_MIDDLE)
        first = r.choice(FEMALE_FIRST if is_female else MALE_FIRST)
        name = f"{family} {middle} {first}"
        attempt = 0
        while name in used_names:
            attempt += 1
            middle = r.choice(FEMALE_MIDDLE if is_female else MALE_MIDDLE)
            first = r.choice(FEMALE_FIRST if is_female else MALE_FIRST)
            name = f"{family} {middle} {first}"
            if attempt > 20:
                name = f"{family} {middle} {first} {attempt}"
        used_names.add(name)

        dept_name = r.choices(dept_names_list, weights=dept_weights, k=1)[0]
        dept_pos = dept_positions[dept_name]
        non_lead = [p for p in dept_pos if "Trưởng" not in p.name and "Giám đốc" not in p.name
                     and "Kế toán trưởng" not in p.name and "CEO" not in p.name and "CTO" not in p.name and "CFO" not in p.name]
        pos_obj = r.choice(non_lead or dept_pos)
        pos_name = pos_obj.name

        dob = date(r.randint(1985, 2002), r.randint(1, 12), r.randint(1, 28))
        start = date(r.randint(2019, 2025), r.randint(1, 12), r.randint(1, 28))
        is_active = i not in inactive_indices

        emp = create_employee(name, gender, dept_name, pos_name, dob, start, is_active)
        manager = get_dept_manager(dept_name)
        if manager and manager.full_name != name:
            emp.manager_id = manager.id
        employees.append(emp)
        session.add(emp)

    await session.flush()
    return employees


async def seed_job_openings(
    session: AsyncSession,
    positions: dict[str, Position],
) -> list[JobOpening]:
    r = rng()
    openings: list[JobOpening] = []

    opening_specs = [
        ("Senior Backend Developer", "open", 3),
        ("Senior Frontend Developer", "open", 2),
        ("Junior Frontend Developer", "open", 4),
        ("Junior Backend Developer", "open", 3),
        ("DevOps Engineer", "open", 2),
        ("QA/Tester", "open", 2),
        ("UI/UX Designer", "open", 1),
        ("Business Analyst", "open", 1),
        ("Chuyên viên Tuyển dụng", "open", 2),
        ("Nhân viên Kinh Doanh", "open", 5),
        ("CSKH (Chăm sóc khách hàng)", "open", 3),
        ("Kế toán viên", "closed", 1),
    ]

    for pos_name, status, headcount in opening_specs:
        desc = (
            f"Vroom HR đang tìm kiếm {pos_name}. "
            f"Yêu cầu: kinh nghiệm phù hợp, kỹ năng chuyên môn tốt, "
            f"đam mê công nghệ nhân sự. Ưu tiên ứng viên có kinh nghiệm "
            f"làm việc với sản phẩm SaaS/B2B."
        )
        jo = JobOpening(
            id=uuid4(),
            title=pos_name,
            description=desc,
            position_id=positions[pos_name].id,
            target_headcount=headcount,
            status=status,
            opened_at=datetime.now(UTC) - timedelta(days=r.randint(7, 90)) if status != "draft" else None,
        )
        session.add(jo)
        openings.append(jo)

    await session.flush()
    return openings


async def seed_candidates(
    session: AsyncSession,
    job_openings: list[JobOpening],
    count: int = 55,
) -> list[Candidate]:
    r = rng()
    candidates: list[Candidate] = []
    statuses = ["new", "reviewing", "interview_scheduled", "accepted", "rejected", "archived"]
    status_weights = [15, 25, 25, 8, 17, 10]
    companies = [
        "FPT Software", "VNG", "Shopee", "Tiki", "MoMo", "Vingroup",
        "VNPT", "Viettel", "Nashtech", "KMS Technology", "Axon Active",
        "TMA Solutions", "Haravan", "Sendo", "Topica", "VCCorp",
    ]

    for i in range(count):
        is_female = r.random() < 0.40
        gender = "female" if is_female else "male"
        family = r.choice(FAMILY_NAMES)
        middle = r.choice(FEMALE_MIDDLE if is_female else MALE_MIDDLE)
        first = r.choice(FEMALE_FIRST if is_female else MALE_FIRST)
        name = f"{family} {middle} {first}"

        first_lower = first.lower().replace(" ", "")
        family_lower = family.lower().replace(" ", "")
        email = f"{first_lower}.{family_lower}{r.randint(0, 999)}@gmail.com"

        status = r.choices(statuses, weights=status_weights, k=1)[0]
        skills = r.sample(SKILLS_POOL, k=min(r.randint(3, 8), len(SKILLS_POOL)))
        jo = r.choice(job_openings) if r.random() < 0.7 else None

        exp_years = r.randint(0, 12)
        experience = []
        if exp_years > 0:
            num_jobs = min(exp_years, r.randint(1, 3))
            for j in range(num_jobs):
                start_year = 2025 - exp_years + j * max(1, exp_years // num_jobs)
                experience.append({
                    "company": r.choice(companies),
                    "title": r.choice(["Software Engineer", "Developer", "Senior Dev", "Tech Lead", "Intern"]),
                    "from": f"{start_year}-{r.randint(1,12):02d}",
                    "to": f"{start_year + max(1, exp_years // num_jobs)}-{r.randint(1,12):02d}" if j < num_jobs - 1 else "Hiện tại",
                })

        education = [{
            "school": r.choice([
                "Đại học Bách Khoa Hà Nội", "ĐH Khoa Học Tự Nhiên",
                "ĐH Công Nghệ Thông Tin", "Đại học FPT", "RMIT Vietnam",
                "Đại học Kinh Tế TP.HCM", "Đại học Ngoại Thương",
            ]),
            "degree": r.choice(["Cử nhân", "Kỹ sư", "Thạc sĩ"]),
            "major": r.choice([
                "Công nghệ thông tin", "Khoa học máy tính",
                "Kỹ thuật phần mềm", "Quản trị kinh doanh",
                "Tài chính - Ngân hàng", "Marketing",
            ]),
            "year": str(r.randint(2010, 2023)),
        }]

        c = Candidate(
            id=uuid4(),
            name=name,
            email=email,
            phone=vn_phone(r),
            skills=skills,
            experience=experience,
            education=education,
            summary=f"Ứng viên {name} có {exp_years} năm kinh nghiệm trong lĩnh vực {', '.join(skills[:3])}.",
            status=status,
            confidence_score=round(r.uniform(0.3, 0.98), 2),
            job_opening_id=jo.id if jo else None,
        )

        if status == "rejected":
            c.rejected_at = datetime.now(UTC) - timedelta(days=r.randint(1, 30))
            c.rejection_reason = r.choice([
                "Không phù hợp văn hóa công ty",
                "Thiếu kỹ năng chuyên môn cần thiết",
                "Ứng viên từ chối offer",
                "Đã chọn ứng viên phù hợp hơn",
            ])
        if status == "accepted":
            c.accepted_at = datetime.now(UTC) - timedelta(days=r.randint(1, 14))
        if status == "archived":
            c.archived_at = datetime.now(UTC) - timedelta(days=r.randint(1, 60))

        session.add(c)
        candidates.append(c)

    await session.flush()
    return candidates


async def seed_interviews(
    session: AsyncSession,
    candidates: list[Candidate],
    employees: list[Employee],
    count: int = 50,
) -> list[Interview]:
    r = rng()
    interviews: list[Interview] = []
    statuses = ["scheduled", "completed", "cancelled"]
    status_weights = [30, 55, 15]
    rounds = ["Vòng 1 - Phone Screen", "Vòng 2 - Technical", "Vòng 3 - Culture Fit", "Vòng 4 - Final"]

    interviewing = [c for c in candidates if c.status in ("interviewing", "offered", "accepted", "new", "screening")]
    if not interviewing:
        interviewing = candidates[:count]

    for i in range(min(count, len(interviewing))):
        candidate = interviewing[i % len(interviewing)]
        status = r.choices(statuses, weights=status_weights, k=1)[0]

        if status == "completed":
            days_ago = r.randint(1, 30)
            start = datetime.now(UTC) - timedelta(days=days_ago, hours=r.randint(0, 8))
        elif status == "scheduled":
            days_ahead = r.randint(1, 14)
            start = datetime.now(UTC) + timedelta(days=days_ahead, hours=r.randint(0, 8))
        else:
            days_ago = r.randint(1, 20)
            start = datetime.now(UTC) - timedelta(days=days_ago)

        # Round to nearest hour
        start = start.replace(minute=0, second=0, microsecond=0)

        interview = Interview(
            id=uuid4(),
            candidate_id=candidate.id,
            status=status,
            round_name=r.choice(rounds),
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone="Asia/Ho_Chi_Minh",
            meeting_mode="google_meet",
        )
        session.add(interview)
        interviews.append(interview)

        # Candidate participant
        session.add(InterviewParticipant(
            id=uuid4(),
            interview_id=interview.id,
            type="candidate",
            email=candidate.email,
            name=candidate.name,
        ))

        # 1-2 employee interviewers
        for _ in range(r.randint(1, 2)):
            emp = r.choice(employees)
            session.add(InterviewParticipant(
                id=uuid4(),
                interview_id=interview.id,
                type="employee",
                email=emp.email,
                name=emp.full_name,
                employee_id=emp.id,
                response_status=r.choice(["accepted", "tentative", "needsAction"]),
            ))

    await session.flush()
    return interviews


async def seed_attendance(
    session: AsyncSession,
    employees: list[Employee],
) -> list[AttendanceRecord]:
    r = rng()
    records: list[AttendanceRecord] = []

    today_hcm = datetime.now(UTC).astimezone(HCM).date()
    # Last 4 weeks Monday
    monday = today_hcm - timedelta(days=today_hcm.weekday() + 28)
    workdays = []
    for d in range(56):
        day = monday + timedelta(days=d)
        if day >= today_hcm:
            break
        if day.weekday() < 5:
            workdays.append(day)

    active_employees = [e for e in employees if e.is_active]

    for emp in active_employees:
        for wd in workdays:
            if r.random() < 0.05:  # 5% absent
                continue

            # Check-in time
            check_in_hour = r.choices([8, 9, 10], weights=[60, 25, 15], k=1)[0]
            check_in_min = r.randint(0, 59)
            check_in = datetime(wd.year, wd.month, wd.day, check_in_hour, check_in_min, 0, tzinfo=HCM).astimezone(UTC)

            check_out = None
            if r.random() < 0.85:  # 85% check out
                out_h = 17 + r.randint(0, 2)
                out_m = r.randint(0, 59)
                check_out = datetime(wd.year, wd.month, wd.day, out_h, out_m, 0, tzinfo=HCM).astimezone(UTC)

            ip = f"192.168.{r.randint(1, 255)}.{r.randint(1, 254)}"
            record = AttendanceRecord(
                id=uuid4(),
                employee_id=emp.id,
                work_date=wd,
                check_in_at=check_in,
                check_out_at=check_out,
                check_in_ip=ip,
                check_out_ip=ip if check_out else None,
                check_in_user_agent="VroomHR-Web/1.0",
                check_out_user_agent="VroomHR-Web/1.0" if check_out else None,
                source=r.choice([AttendanceSource.WEB, AttendanceSource.WEB, AttendanceSource.MOBILE]),
            )
            session.add(record)
            records.append(record)

    await session.flush()
    return records


async def seed_payslips(
    session: AsyncSession,
    employees: list[Employee],
    depts: dict[str, Department],
) -> list[Payslip]:
    r = rng()
    payslips: list[Payslip] = []

    active_employees = [e for e in employees if e.is_active]
    today = date.today()

    # Last 3 months
    period_months: list[date] = []
    for i in range(1, 4):
        month = today.month - i
        year = today.year
        while month < 1:
            month += 12
            year -= 1
        period_months.append(date(year, month, 1))

    # Build dept_id -> name mapping for salary ranges
    dept_id_to_name: dict[UUID, str] = {d.id: name for name, d in depts.items()}

    # Salary ranges
    dept_salary_ranges = {
        "Ban Giám Đốc": (30_000_000, 60_000_000),
        "Phòng Kỹ Thuật": (15_000_000, 40_000_000),
        "Phòng Sản Phẩm": (15_000_000, 35_000_000),
        "Phòng Nhân Sự": (10_000_000, 25_000_000),
        "Phòng Kinh Doanh": (8_000_000, 30_000_000),
        "Phòng Tài Chính - Kế Toán": (10_000_000, 28_000_000),
    }

    for emp in active_employees:
        dept_name = dept_id_to_name.get(emp.department_id, "")
        lo, hi = dept_salary_ranges.get(dept_name, (10_000_000, 20_000_000))
        base_salary = r.randint(lo, hi) // 500_000 * 500_000  # Round to 500k

        for pm in period_months:
            # Add slight variation per month
            salary = base_salary + r.randint(-500_000, 1_000_000)
            salary = max(5_000_000, salary)

            insurance = max(0, round(salary * 0.105))
            personal_deduction = 11_000_000
            taxable = max(0, salary - insurance - personal_deduction)
            if taxable <= 0:
                pit = 0
            elif taxable <= 5_000_000:
                pit = round(taxable * 0.05)
            elif taxable <= 10_000_000:
                pit = round(taxable * 0.10)
            elif taxable <= 18_000_000:
                pit = round(taxable * 0.15)
            else:
                pit = round(taxable * 0.20)
            net = salary - insurance - pit

            payslip = Payslip(
                id=uuid4(),
                employee_id=emp.id,
                period_month=pm,
                gross_salary=Decimal(str(salary)),
                deductions=Decimal(str(insurance + pit)),
                insurance_employee=Decimal(str(insurance)),
                taxable_income=Decimal(str(max(0, salary - insurance))),
                pit_amount=Decimal(str(pit)),
                net_salary=Decimal(str(net)),
                currency="VND",
                status=PayslipStatus.PUBLISHED,
                published_at=datetime.now(UTC) - timedelta(days=r.randint(1, 15)),
            )
            session.add(payslip)
            payslips.append(payslip)

    await session.flush()
    return payslips


async def seed_onboarding(
    session: AsyncSession,
    employees: list[Employee],
    candidates: list[Candidate],
    admin: User,
    count: int = 15,
) -> list[OnboardingProcess]:
    r = rng()
    processes: list[OnboardingProcess] = []

    accepted = [c for c in candidates if c.status == "accepted"]
    targets = accepted[:min(count, len(accepted))]

    task_templates = [
        ("personal_info", "Cập nhật thông tin cá nhân"),
        ("documents", "Nộp giấy tờ (CCCD, bằng cấp)"),
        ("equipment", "Nhận thiết bị làm việc"),
        ("orientation", "Tham gia buổi định hướng"),
    ]

    for i, candidate in enumerate(targets):
        emp = employees[i % len(employees)]
        status = r.choice(["in_progress", "in_progress", "in_progress", "complete"])

        proc = OnboardingProcess(
            id=uuid4(),
            candidate_id=candidate.id,
            employee_id=emp.id,
            status=status,
            completed_at=datetime.now(UTC) - timedelta(days=r.randint(1, 30)) if status == "complete" else None,
        )
        session.add(proc)
        processes.append(proc)

        for idx, (task_key, task_name) in enumerate(task_templates):
            task_done = (status == "complete") or (status == "in_progress" and r.random() < 0.5)
            session.add(OnboardingTask(
                id=uuid4(),
                process_id=proc.id,
                task_key=task_key,
                name=task_name,
                status="done" if task_done else "pending",
                order_index=idx,
                completed_at=datetime.now(UTC) - timedelta(days=r.randint(1, 14)) if task_done else None,
                completed_by_user_id=admin.id if task_done else None,
            ))

    await session.flush()
    return processes


async def seed_employee_requests(
    session: AsyncSession,
    employees: list[Employee],
    admin: User,
    count: int = 60,
) -> list[EmployeeRequest]:
    r = rng()
    requests: list[EmployeeRequest] = []

    active_employees = [e for e in employees if e.is_active]
    today = date.today()

    for i in range(count):
        emp = r.choice(active_employees)
        req_type = r.choice([RequestType.LEAVE, RequestType.LEAVE, RequestType.LEAVE, RequestType.OVERTIME])
        status = r.choices(
            [RequestStatus.SUBMITTED, RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED],
            weights=[25, 55, 15, 5],
            k=1,
        )[0]

        reviewed_by = admin.id if status in (RequestStatus.APPROVED, RequestStatus.REJECTED) else None
        reviewed_at = datetime.now(UTC) - timedelta(days=r.randint(0, 14)) if reviewed_by else None

        if req_type == RequestType.LEAVE:
            leave_type = r.choice([LeaveType.ANNUAL, LeaveType.SICK, LeaveType.UNPAID, LeaveType.OTHER])
            if status != RequestStatus.SUBMITTED:
                start_date = today - timedelta(days=r.randint(1, 30))
            else:
                start_date = today + timedelta(days=r.randint(1, 14))
            end_date = start_date + timedelta(days=r.randint(0, 3))

            reason_map = {
                LeaveType.ANNUAL: r.choice(["Nghỉ phép năm", "Về quê thăm gia đình", "Du lịch", "Việc cá nhân"]),
                LeaveType.SICK: r.choice(["Ốm, sốt cao", "Đau dạ dày", "Viêm họng cấp", "Khám sức khỏe định kỳ"]),
                LeaveType.UNPAID: r.choice(["Việc gia đình khẩn cấp", "Chưa có phép năm", "Nghỉ dài hạn"]),
                LeaveType.OTHER: r.choice(["Đám cưới người thân", "Tang lễ", "Thi cử", "Hội thảo"]),
            }
            reason = reason_map.get(leave_type, "Lý do cá nhân")

            req = EmployeeRequest(
                id=uuid4(),
                employee_id=emp.id,
                request_type=req_type,
                status=status,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                reviewed_by_user_id=reviewed_by,
                reviewed_at=reviewed_at,
                review_reason=(
                    "Không đủ điều kiện" if status == RequestStatus.REJECTED
                    else ("Đã duyệt" if status == RequestStatus.APPROVED else None)
                ),
            )
        else:  # OVERTIME
            work_date = today - timedelta(days=r.randint(1, 14))
            start_h = r.randint(17, 19)
            end_h = r.randint(20, 23)
            req = EmployeeRequest(
                id=uuid4(),
                employee_id=emp.id,
                request_type=RequestType.OVERTIME,
                status=status,
                work_date=work_date,
                start_time=time(start_h, 0),
                end_time=time(end_h, 0),
                duration_minutes=(end_h - start_h) * 60,
                reason=r.choice([
                    "Hoàn thành sprint", "Fix bug khẩn cấp",
                    "Deploy phiên bản mới", "Hỗ trợ khách hàng",
                    "Chuẩn bị báo cáo cuối tháng",
                ]),
                project_or_task=r.choice([
                    "Dự án Vroom HR", "Hệ thống Payroll",
                    "Migration Database", "Release 2.0",
                ]),
                reviewed_by_user_id=reviewed_by,
                reviewed_at=reviewed_at,
                review_reason=(
                    r.choice(["Không cần thiết", "Ngân sách OT đã hết"])
                    if status == RequestStatus.REJECTED
                    else ("Đã duyệt" if status == RequestStatus.APPROVED else None)
                ),
            )

        session.add(req)
        requests.append(req)

    await session.flush()
    return requests


# ── Main ────────────────────────────────────────────────────────────

async def main() -> None:
    engine = create_async_engine(DB_URL, echo=False)

    async with AsyncSession(engine) as session:
        print("=" * 60)
        print("  VROOM HR — SEED ALL DEMO DATA (Vietnamese)")
        print("=" * 60)

        org = await seed_organization(session)
        print(f"✓ Organization: {org.name}")

        depts = await seed_departments(session)
        print(f"✓ Departments: {len(depts)}")

        positions = await seed_positions(session, depts)
        print(f"✓ Positions: {len(positions)}")

        admin = await seed_admin_user(session)
        print(f"✓ Admin user: {admin.email} (password: admin123)")

        employees = await seed_employees(session, depts, positions, admin, count=55)
        print(f"✓ Employees: {len(employees)}")

        job_openings = await seed_job_openings(session, positions)
        print(f"✓ Job Openings: {len(job_openings)}")

        candidates = await seed_candidates(session, job_openings, count=55)
        print(f"✓ Candidates: {len(candidates)}")

        interviews = await seed_interviews(session, candidates, employees, count=50)
        print(f"✓ Interviews: {len(interviews)}")

        attendance = await seed_attendance(session, employees)
        print(f"✓ Attendance Records: {len(attendance)}")

        payslips = await seed_payslips(session, employees, depts)
        print(f"✓ Payslips: {len(payslips)}")

        onboarding = await seed_onboarding(session, employees, candidates, admin, count=15)
        print(f"✓ Onboarding Processes: {len(onboarding)}")

        emp_requests = await seed_employee_requests(session, employees, admin, count=60)
        print(f"✓ Employee Requests: {len(emp_requests)}")

        await session.commit()

        print("=" * 60)
        print("  ✅ SEED COMPLETE!")
        print(f"  🔑 Login: hr@vroom.com / admin123")
        print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
