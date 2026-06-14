"""Employee Assistant Service — orchestrates the tool-calling loop.

Shares the AssistantLLMClient singleton with the HR Assistant, but uses its
own system prompt and tool set (employee-scoped). The tool-calling loop is
identical to the HR Assistant (see ADR-0003 for architecture rationale).

This service is created per-request with the authenticated employee_id,
ensuring every tool call is scoped to that employee.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.modules.assistant.application.employee_tool_registry import (
    EmployeeToolRegistry,
)
from src.modules.assistant.application.assistant_service import ChatMessage, ChatResponse
from src.modules.assistant.infrastructure.config import AssistantSettings
from src.modules.assistant.infrastructure.llm_client import AssistantLLMClient

if TYPE_CHECKING:
    from src.modules.attendance.infrastructure.attendance_record_repository import (
        AttendanceRecordRepository,
    )
    from src.modules.employee.application.employee_service import EmployeeService
    from src.modules.employee_request.application.leave_service import LeaveService
    from src.modules.employee_request.application.overtime_service import OvertimeService
    from src.modules.payslip.application.payslip_service import PayslipService

logger = logging.getLogger(__name__)

_MAX_TOOL_ITERATIONS = 5

_TOOL_LOOP_FALLBACK = (
    "Xin lỗi, trợ lý đã xử lý quá nhiều bước. Vui lòng thử lại với câu hỏi cụ thể hơn."
)

_EMPLOYEE_SYSTEM_PROMPT = """You are the Employee Assistant for Vroom HR.

You help active employees with their own HR data.
You speak Vietnamese when the employee speaks Vietnamese, English otherwise.

Rules:
- You can ONLY access the current employee's own data — never ask for
  another employee's information.
- You NEVER write to the database directly.
- You only propose actions for the employee to review and confirm
  (human-in-the-loop).
- For Read-Tools: call them to answer data questions accurately.
- For Draft-Tools: use them when the employee asks to submit a leave
  or overtime request — the tool returns a draft for preview.
- Be concise and helpful. Use Vietnamese when the employee does.
- If a tool fails, tell the employee clearly and suggest they try again.
"""


class EmployeeAssistantService:
    """Orchestrates the Employee AI Assistant conversation loop.

    Created per-request with the authenticated employee_id. Uses the shared
    AssistantLLMClient singleton (ADR-0007) and its own tool set.

    Args:
        llm_client: The assistant's own LLM client (shared singleton).
        employee_id: The authenticated employee's UUID.
        employee_service: For profile reads.
        attendance_repo: For attendance record reads.
        leave_service: For leave request reads.
        overtime_service: For overtime request reads.
        payslip_service: For payslip reads.
        settings: Assistant settings with max_history, etc.
    """

    def __init__(
        self,
        llm_client: AssistantLLMClient,
        employee_id: UUID,
        employee_service: EmployeeService,
        attendance_repo: AttendanceRecordRepository,
        leave_service: LeaveService,
        overtime_service: OvertimeService,
        payslip_service: PayslipService,
        settings: AssistantSettings,
    ) -> None:
        self._llm_client = llm_client
        self._employee_id = employee_id
        self._employee_service = employee_service
        self._attendance_repo = attendance_repo
        self._leave_service = leave_service
        self._overtime_service = overtime_service
        self._payslip_service = payslip_service
        self._settings = settings

    async def chat(
        self,
        messages: list[ChatMessage],
    ) -> ChatResponse:
        """Process a user message through the tool-calling loop.

        Args:
            messages: Full conversation history including the new user message.

        Returns:
            ChatResponse with updated messages and optional draft_action.
        """
        tool_registry = EmployeeToolRegistry(
            employee_id=self._employee_id,
            employee_service=self._employee_service,
            attendance_repo=self._attendance_repo,
            leave_service=self._leave_service,
            overtime_service=self._overtime_service,
            payslip_service=self._payslip_service,
        )

        openai_messages = self._build_messages(messages, tool_registry)

        draft_action: dict[str, Any] | None = None
        all_new_messages: list[ChatMessage] = []

        for _iteration in range(_MAX_TOOL_ITERATIONS):
            response = await self._llm_client.chat(
                messages=openai_messages,
                tools=tool_registry.get_openai_tools(),
            )

            if not response.tool_calls:
                assistant_msg = ChatMessage(
                    role="assistant",
                    content=response.content or "",
                )
                all_new_messages.append(assistant_msg)
                break

            assistant_msg = ChatMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            all_new_messages.append(assistant_msg)

            assistant_openai: dict[str, Any] = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": response.tool_calls,
            }
            openai_messages.append(assistant_openai)

            for tc in response.tool_calls:
                tool_name = tc["function"]["name"]
                try:
                    tool_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    tool_args = {}

                result_str = await tool_registry.execute(tool_name, tool_args)

                if tool_registry.is_draft_tool(tool_name):
                    try:
                        result_data = json.loads(result_str)
                        if "draft_action" in result_data:
                            draft_action = result_data["draft_action"]
                    except json.JSONDecodeError:
                        pass

                tool_msg = ChatMessage(
                    role="tool",
                    content=result_str,
                    tool_call_id=tc["id"],
                    name=tool_name,
                )
                all_new_messages.append(tool_msg)

                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_str,
                    }
                )

        has_text_response = any(
            m.role == "assistant" and m.content for m in all_new_messages
        )
        if not has_text_response:
            all_new_messages.append(
                ChatMessage(role="assistant", content=_TOOL_LOOP_FALLBACK)
            )

        return ChatResponse(
            messages=all_new_messages,
            draft_action=draft_action,
        )

    def _build_messages(
        self,
        messages: list[ChatMessage],
        tool_registry: EmployeeToolRegistry,
    ) -> list[dict]:
        """Build OpenAI-format messages with employee system prompt."""
        tools = tool_registry.get_openai_tools()
        tools_str = "\n".join(
            f"{i + 1}. {t['function']['name']} — {t['function']['description']}"
            for i, t in enumerate(tools)
        )

        system_content = (
            _EMPLOYEE_SYSTEM_PROMPT
            + f"\nYou have access to these tools:\n{tools_str}\n"
        )

        result: list[dict[str, Any]] = [
            {"role": "system", "content": system_content}
        ]

        start_idx = max(0, len(messages) - self._settings.max_history)
        while start_idx > 0 and messages[start_idx].role != "user":
            start_idx -= 1
        history = messages[start_idx:]

        for msg in history:
            if msg.role == "tool":
                logger.warning(
                    "Stripped unexpected tool message from client history"
                )
                continue

            if msg.role == "assistant" and msg.content is None:
                logger.warning(
                    "Stripped assistant history message without content"
                )
                continue

            entry: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                entry["content"] = msg.content

            if msg.role == "assistant" and msg.tool_calls and msg.content is None:
                entry["tool_calls"] = msg.tool_calls

            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.name:
                entry["name"] = msg.name
            result.append(entry)

        return result
