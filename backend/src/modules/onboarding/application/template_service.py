"""Application service for onboarding template management."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.domain.entities import User
from src.modules.onboarding.domain.entities import OnboardingAuditLog, OnboardingTemplate
from src.modules.onboarding.infrastructure.audit_repository import OnboardingAuditRepository
from src.modules.onboarding.infrastructure.template_repository import OnboardingTemplateRepository

_OP_TEMPLATE_CREATED = "template_created"
_OP_TEMPLATE_UPDATED = "template_updated"
_OP_TEMPLATE_ARCHIVED = "template_archived"


class OnboardingTemplateService:
    """Manage reusable onboarding templates and audit template changes."""

    def __init__(
        self,
        template_repo: OnboardingTemplateRepository,
        audit_repo: OnboardingAuditRepository,
        session: AsyncSession,
    ) -> None:
        self.template_repo = template_repo
        self.audit_repo = audit_repo
        self.session = session

    async def list_templates(
        self,
        template_type: str | None = None,
        include_archived: bool = False,
    ) -> list[OnboardingTemplate]:
        return await self.template_repo.list(template_type, include_archived)

    async def create_template(
        self,
        actor: User,
        data: dict[str, Any],
    ) -> OnboardingTemplate:
        existing = await self.template_repo.get_by_key(data["template_type"], data["key"])
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail={"code": "TEMPLATE_DUPLICATE"},
            )
        template = OnboardingTemplate(**data)
        await self.template_repo.create(template)
        await self._append_audit(
            actor=actor,
            operation_type=_OP_TEMPLATE_CREATED,
            template=template,
            previous_value=None,
            new_value=self._serialize(template),
        )
        await self.session.commit()
        return template

    async def update_template(
        self,
        template_id: UUID,
        actor: User,
        data: dict[str, Any],
    ) -> OnboardingTemplate:
        template = await self._get_required_template(template_id)
        previous_value = self._serialize(template)
        for field, value in data.items():
            setattr(template, field, value)
        template.bump_version()
        template.updated_at = datetime.now(UTC)
        await self.template_repo.update(template)
        await self._append_audit(
            actor=actor,
            operation_type=_OP_TEMPLATE_UPDATED,
            template=template,
            previous_value=previous_value,
            new_value=self._serialize(template),
        )
        await self.session.commit()
        return template

    async def archive_template(self, template_id: UUID, actor: User) -> OnboardingTemplate:
        template = await self._get_required_template(template_id)
        previous_value = self._serialize(template)
        template.archive()
        await self.template_repo.update(template)
        await self._append_audit(
            actor=actor,
            operation_type=_OP_TEMPLATE_ARCHIVED,
            template=template,
            previous_value=previous_value,
            new_value=self._serialize(template),
        )
        await self.session.commit()
        return template

    async def preview_template(self, template_id: UUID) -> dict[str, Any]:
        template = await self._get_required_template(template_id)
        return {
            "id": str(template.id),
            "template_type": template.template_type,
            "preview": self._render_preview(template),
        }

    async def ensure_seed_templates(
        self, templates: list[OnboardingTemplate]
    ) -> list[OnboardingTemplate]:
        existing = await self.template_repo.list(include_archived=True)
        existing_keys = {(row.template_type, row.key) for row in existing}
        to_create = [
            template
            for template in templates
            if (template.template_type, template.key) not in existing_keys
        ]
        for template in to_create:
            await self.template_repo.create(template)
        if to_create:
            await self.session.commit()
        return to_create

    async def _get_required_template(self, template_id: UUID) -> OnboardingTemplate:
        template = await self.template_repo.get_by_id(template_id)
        if template is None:
            raise ValueError("Template not found")
        return template

    async def _append_audit(
        self,
        actor: User,
        operation_type: str,
        template: OnboardingTemplate,
        previous_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
    ) -> None:
        entry = OnboardingAuditLog(
            user_id=actor.id,
            actor_email=actor.email,
            operation_type=operation_type,
            entity_type="template",
            entity_id=template.id,
            previous_value=previous_value,
            new_value=new_value,
            change_summary=f"{operation_type}: {template.template_type}/{template.key}",
        )
        await self.audit_repo.append(entry)

    def _serialize(self, template: OnboardingTemplate) -> dict[str, Any]:
        return {
            "id": str(template.id),
            "template_type": template.template_type,
            "key": template.key,
            "display_name": template.display_name,
            "description": template.description,
            "template_body": template.template_body,
            "is_required": template.is_required,
            "order_index": template.order_index,
            "version": template.version,
            "is_system": template.is_system,
            "is_archived": template.is_archived,
        }

    def _render_preview(self, template: OnboardingTemplate) -> str:
        if template.template_type == "contract":
            body = template.template_body or template.description or template.display_name
            return (
                body.replace("{{candidate_name}}", "Nguyễn Văn A")
                .replace("{{employee_code}}", "NV-001")
                .replace("{{process_id}}", "00000000-0000-0000-0000-000000000000")
                .replace("{{candidate_id}}", "11111111-1111-1111-1111-111111111111")
            )
        if template.template_type == "task":
            description = template.description or ""
            return f"{template.order_index + 1}. {template.display_name} — {description}"
        required = "Required" if template.is_required else "Optional"
        description = template.description or ""
        return f"[{required}] {template.display_name}: {description}"
