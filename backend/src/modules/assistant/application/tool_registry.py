"""Tool registry — executes Read-Tools and wraps Draft-Tools.

Backend executes all tools directly (grill decision: "Backend tự execute
tool, không qua LLM function calling"). The LLM only defines WHAT to call;
the backend runs the actual logic.

Read-Tools call into recruitment/onboarding services (ADR-0004: one-way
dependency from assistant → other modules' services).

Draft-Tools do NOT execute a write. They return a structured Draft Action
(ADR-0006). HR reviews it; on confirm, the frontend calls the real endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from src.modules.assistant.domain.tools import DraftAction, ToolKind

if TYPE_CHECKING:
    from src.modules.onboarding.application.onboarding_service import OnboardingService
    from src.modules.recruitment.application.candidate_service import CandidateService

logger = logging.getLogger(__name__)

# CandidateStatus values from recruitment/domain/enums.py
_VALID_STATUSES = {"new", "reviewing", "interview_scheduled", "accepted", "rejected", "archived"}


class ToolRegistry:
    """Executes tools and returns results for the LLM.

    Injects CandidateService and OnboardingService (read-only usage).
    No write capabilities — structural safety per ADR-0006.

    Args:
        candidate_service: Recruitment CandidateService for read operations.
        onboarding_service: Onboarding OnboardingService for read operations.
    """

    def __init__(
        self,
        candidate_service: CandidateService,
        onboarding_service: OnboardingService,
    ) -> None:
        self._candidate_service = candidate_service
        self._onboarding_service = onboarding_service

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool by name and return the result as JSON string.

        Args:
            tool_name: The tool name from the LLM's tool_call.
            arguments: Parsed arguments from the LLM.

        Returns:
            JSON string result for the LLM to consume.

        Raises:
            ValueError: If the tool name is unknown.
        """
        handlers = {
            "count_candidates_by_status": self._count_candidates_by_status,
            "list_in_progress_onboarding": self._list_in_progress_onboarding,
            "search_candidates": self._search_candidates,
            "draft_email": self._draft_email,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            result = await handler(arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            logger.exception("Tool execution failed: %s", tool_name)
            return json.dumps({"error": f"Tool execution failed: {exc}"})

    def is_draft_tool(self, tool_name: str) -> bool:
        """Check if a tool is a Draft-Tool (returns Draft Action, not data)."""
        from src.modules.assistant.domain.tools import TOOL_DEFINITIONS

        for t in TOOL_DEFINITIONS:
            if t.name == tool_name and t.kind == ToolKind.DRAFT:
                return True
        return False

    async def _count_candidates_by_status(self, args: dict[str, Any]) -> dict:
        """Read-Tool: count candidates grouped by status."""
        status_filter = args.get("status")

        if status_filter:
            if status_filter not in _VALID_STATUSES:
                valid = sorted(_VALID_STATUSES)
                return {"error": f"Invalid status: {status_filter}. Valid: {valid}"}
            result = await self._candidate_service.list_candidates(
                status=[status_filter], page=1, page_size=1
            )
            return {"status": status_filter, "count": result.total_count}

        counts = {}
        for s in sorted(_VALID_STATUSES):
            result = await self._candidate_service.list_candidates(
                status=[s], page=1, page_size=1
            )
            counts[s] = result.total_count
        return {"counts": counts, "total": sum(counts.values())}

    async def _list_in_progress_onboarding(self, args: dict[str, Any]) -> dict:
        """Read-Tool: list onboarding processes that are in_progress."""
        result = await self._onboarding_service.list_processes(
            status="in_progress", page=1, page_size=50
        )
        items = []
        for item in result.items:
            items.append(
                {
                    "process_id": str(item.process_id),
                    "employee_id": str(item.employee_id),
                    "completed_count": item.completed_count,
                    "total_count": item.total_count,
                    "status": item.status,
                }
            )
        return {"processes": items, "total": result.total}

    async def _search_candidates(self, args: dict[str, Any]) -> dict:
        """Read-Tool: search candidates by name or email."""
        query = args.get("query", "")
        if not query:
            return {"error": "Query is required"}

        result = await self._candidate_service.list_candidates(
            search=query, page=1, page_size=10
        )
        candidates = []
        for c in result.candidates:
            candidates.append(
                {
                    "id": str(c.id),
                    "name": c.name,
                    "email": c.email,
                    "status": c.status,
                }
            )
        return {"candidates": candidates, "total": result.total_count}

    async def _draft_email(self, args: dict[str, Any]) -> dict:
        """Draft-Tool: returns a Draft Action for email sending."""
        to = args.get("to", [])
        subject = args.get("subject", "")
        body_html = args.get("body_html", "")

        if not to:
            return {"error": "Recipients (to) are required"}
        if not subject:
            return {"error": "Subject is required"}
        if not body_html:
            return {"error": "Body is required"}

        to_str = ", ".join(to)

        draft = DraftAction(
            action_type="send_email",
            parameters={"to": to, "subject": subject, "body_html": body_html},
            preview=f"Gửi email đến {to_str} với subject: {subject}",
            confirm_endpoint="/api/gmail/send",
            confirm_method="POST",
            confirm_body={"to": to, "subject": subject, "body_html": body_html},
        )

        return {
            "draft_action": {
                "action_type": draft.action_type,
                "parameters": draft.parameters,
                "preview": draft.preview,
                "confirm_endpoint": draft.confirm_endpoint,
                "confirm_method": draft.confirm_method,
                "confirm_body": draft.confirm_body,
            }
        }
