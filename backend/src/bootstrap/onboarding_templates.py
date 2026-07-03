"""Seed defaults for onboarding templates."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.onboarding.domain.entities import OnboardingTemplate

DEFAULT_ONBOARDING_TEMPLATES: list[dict[str, object]] = [
    {
        "template_type": "task",
        "key": "sign_contract",
        "display_name": "Sign Contract",
        "description": "HR chuẩn bị và ký hợp đồng lao động.",
        "order_index": 0,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "task",
        "key": "submit_documents",
        "display_name": "Submit Documents",
        "description": "HR thu thập hồ sơ cần thiết cho employee record.",
        "order_index": 1,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "task",
        "key": "assign_department_position_manager",
        "display_name": "Assign Department Position Manager",
        "description": "Gán department, position, và manager trước ngày bắt đầu.",
        "order_index": 2,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "task",
        "key": "set_start_date",
        "display_name": "Set Start Date",
        "description": "Chốt ngày bắt đầu cho onboarding case.",
        "order_index": 3,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "cccd",
        "display_name": "Căn cước công dân",
        "description": "Bản scan CCCD / CMND.",
        "is_required": True,
        "order_index": 0,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "degree",
        "display_name": "Bằng cấp / Chứng chỉ",
        "description": "Bằng cấp, chứng chỉ liên quan.",
        "is_required": True,
        "order_index": 1,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "health_cert",
        "display_name": "Giấy khám sức khỏe",
        "description": "Giấy khám sức khỏe còn hiệu lực.",
        "is_required": True,
        "order_index": 2,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "resume",
        "display_name": "Sơ yếu lý lịch",
        "description": "CV hoặc sơ yếu lý lịch bản đầy đủ.",
        "is_required": True,
        "order_index": 3,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "photo",
        "display_name": "Ảnh thẻ",
        "description": "Ảnh thẻ dùng cho hồ sơ.",
        "is_required": False,
        "order_index": 4,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "insurance",
        "display_name": "Sổ bảo hiểm xã hội",
        "description": "Sổ BHXH hoặc mã số BHXH.",
        "is_required": True,
        "order_index": 5,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "diploma",
        "display_name": "Bằng tốt nghiệp",
        "description": "Bằng tốt nghiệp cao nhất.",
        "is_required": True,
        "order_index": 6,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "document",
        "key": "other",
        "display_name": "Giấy tờ khác",
        "description": "Các giấy tờ HR yêu cầu bổ sung.",
        "is_required": False,
        "order_index": 7,
        "version": 1,
        "is_system": True,
    },
    {
        "template_type": "contract",
        "key": "labor_contract",
        "display_name": "Labor Contract",
        "description": "Mẫu hợp đồng lao động cho onboarding.",
        "template_body": (
            "Labor Contract\n"
            "Candidate: {{candidate_name}}\n"
            "Employee code: {{employee_code}}\n"
            "Process ID: {{process_id}}\n"
        ),
        "is_required": True,
        "order_index": 0,
        "version": 1,
        "is_system": True,
    },
]


async def seed_onboarding_templates(session: AsyncSession) -> list[OnboardingTemplate]:
    """Insert missing default templates and return created rows."""
    from sqlmodel import select

    existing_stmt = select(OnboardingTemplate)
    existing = await session.execute(existing_stmt)
    existing_keys = {(row.template_type, row.key) for row in existing.scalars().all()}
    created: list[OnboardingTemplate] = []
    for payload in DEFAULT_ONBOARDING_TEMPLATES:
        key = (payload["template_type"], payload["key"])
        if key in existing_keys:
            continue
        template = OnboardingTemplate(**payload)
        session.add(template)
        created.append(template)
    if created:
        await session.flush()
    return created
