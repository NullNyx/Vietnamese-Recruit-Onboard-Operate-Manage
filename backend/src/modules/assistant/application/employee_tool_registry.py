"""Tool registry for the Employee Assistant — scoped to one Employee.

Every Read-Tool is hard-wired to the employee_id provided at construction time.
The LLM never receives employee_id as a parameter; it is injected from the
authenticated session. This is the structural safety that enforces "assistant
only reads the Employee's own data" (ADR-0013).

Draft-Tools return a Draft Action — they never write to the database.
The employee reviews the draft; on confirm, the frontend calls the real
write endpoint directly (human-in-the-loop, ADR-0006).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.modules.assistant.domain.employee_tools import EMPLOYEE_TOOL_DEFINITIONS
from src.modules.assistant.domain.tools import DraftAction, ToolKind

if TYPE_CHECKING:
    from src.modules.attendance.infrastructure.attendance_record_repository import (
        AttendanceRecordRepository,
    )
    from src.modules.employee.application.employee_service import EmployeeService
    from src.modules.employee_request.application.leave_service import LeaveService
    from src.modules.employee_request.application.overtime_service import OvertimeService
    from src.modules.payslip.application.payslip_service import PayslipService

logger = logging.getLogger(__name__)


class EmployeeToolRegistry:
    """Executes Employee Assistant tools — scoped to a single employee.

    Args:
        employee_id: The authenticated employee's UUID.
        employee_service: For profile reads.
        attendance_repo: For attendance record reads.
        leave_service: For leave request reads.
        overtime_service: For overtime request reads.
        payslip_service: For payslip reads.
    """

    def __init__(
        self,
        employee_id: UUID,
        employee_service: EmployeeService,
        attendance_repo: AttendanceRecordRepository,
        leave_service: LeaveService,
        overtime_service: OvertimeService,
        payslip_service: PayslipService,
    ) -> None:
        self._employee_id = employee_id
        self._employee_service = employee_service
        self._attendance_repo = attendance_repo
        self._leave_service = leave_service
        self._overtime_service = overtime_service
        self._payslip_service = payslip_service

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool by name, returning JSON-string result.

        Args:
            tool_name: The tool name from the LLM's tool_call.
            arguments: Parsed arguments from the LLM.

        Returns:
            JSON string result for the LLM to consume.
        """
        handlers = {
            "get_my_profile": self._get_my_profile,
            "get_my_attendance": self._get_my_attendance,
            "get_my_employee_requests": self._get_my_employee_requests,
            "get_my_payslips": self._get_my_payslips,
            "draft_leave_request": self._draft_leave_request,
            "draft_overtime_request": self._draft_overtime_request,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            result = await handler(arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            logger.exception("Employee tool execution failed: %s", tool_name)
            return json.dumps({"error": f"Tool execution failed: {exc}"})

    @staticmethod
    def is_draft_tool(tool_name: str) -> bool:
        """Check if a tool is a Draft-Tool (returns Draft Action, not data)."""
        for t in EMPLOYEE_TOOL_DEFINITIONS:
            if t.name == tool_name and t.kind == ToolKind.DRAFT:
                return True
        return False

    # -----------------------------------------------------------------------
    # Read-Tools
    # -----------------------------------------------------------------------

    async def _get_my_profile(self, args: dict[str, Any]) -> dict[str, Any]:
        """Return the authenticated employee's own profile.

        employee_id is injected from the session — the LLM cannot
        specify a different employee.
        """
        from src.modules.employee.domain.entities import Employee

        employee: Employee = await self._employee_service.get_employee(
            self._employee_id,
        )
        return {
            "employee_code": employee.employee_code,
            "full_name": employee.full_name,
            "email": employee.email,
            "phone": employee.phone or "",
            "date_of_birth": str(employee.date_of_birth) if employee.date_of_birth else "",
            "gender": employee.gender or "",
            "address": employee.address or "",
            "department_id": str(employee.department_id) if employee.department_id else "",
            "position_id": str(employee.position_id) if employee.position_id else "",
            "start_date": str(employee.start_date) if employee.start_date else "",
            "contract_type": employee.contract_type or "",
        }

    async def _get_my_attendance(self, args: dict[str, Any]) -> dict[str, Any]:
        """Return the authenticated employee's attendance records.

        Optionally filtered by month/year. All records are scoped to
        the employee_id from the session.
        """
        import datetime

        month = args.get("month")
        year = args.get("year")

        now = datetime.date.today()
        if month is None:
            month = now.month
        if year is None:
            year = now.year

        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1)
        else:
            end_date = datetime.date(year, month + 1, 1)

        records = await self._attendance_repo.get_by_employee_and_date_range(
            employee_id=self._employee_id,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "month": month,
            "year": year,
            "records": [
                {
                    "work_date": str(r.work_date),
                    "check_in_at": str(r.check_in_at) if r.check_in_at else "",
                    "check_out_at": str(r.check_out_at) if r.check_out_at else "",
                    "source": r.source.value if r.source else "",
                }
                for r in records
            ],
        }

    async def _get_my_employee_requests(self, args: dict[str, Any]) -> dict[str, Any]:
        """Return the authenticated employee's own requests.

        Optionally filtered by request_type (leave or overtime).
        """
        request_type = args.get("request_type")

        leaves = await self._leave_service.list_my_leaves(self._employee_id)
        overtime = await self._overtime_service.list_my_overtime(self._employee_id)

        items = []

        if request_type is None or request_type == "leave":
            for r in leaves:
                items.append({
                    "id": str(r.id),
                    "type": "leave",
                    "status": r.status.value,
                    "leave_type": r.leave_type.value if r.leave_type else "",
                    "start_date": str(r.start_date) if r.start_date else "",
                    "end_date": str(r.end_date) if r.end_date else "",
                    "reason": r.reason or "",
                    "submitted_at": str(r.submitted_at) if r.submitted_at else "",
                })

        if request_type is None or request_type == "overtime":
            for r in overtime:
                items.append({
                    "id": str(r.id),
                    "type": "overtime",
                    "status": r.status.value,
                    "work_date": str(r.work_date) if r.work_date else "",
                    "start_time": str(r.start_time) if r.start_time else "",
                    "end_time": str(r.end_time) if r.end_time else "",
                    "reason": r.reason or "",
                    "project_or_task": r.project_or_task or "",
                    "submitted_at": str(r.submitted_at) if r.submitted_at else "",
                })

        items.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)

        return {"requests": items}

    async def _get_my_payslips(self, args: dict[str, Any]) -> dict[str, Any]:
        """Return the authenticated employee's own published payslips."""
        payslips = await self._payslip_service.get_my_payslips(self._employee_id)

        return {
            "payslips": [
                {
                    "id": str(p.id),
                    "period_start": str(p.period_start),
                    "period_end": str(p.period_end),
                    "gross_salary": float(p.gross_salary),
                    "net_salary": float(p.net_salary),
                    "basic_salary": float(p.basic_salary),
                    "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                }
                for p in payslips
            ],
        }

    # -----------------------------------------------------------------------
    # Draft-Tools — return DraftAction, NEVER write to DB
    # -----------------------------------------------------------------------

    async def _draft_leave_request(self, args: dict[str, Any]) -> dict[str, Any]:
        """Draft-Tool: returns a Draft Action for a leave request."""
        leave_type = args.get("leave_type")
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        reason = args.get("reason")

        if not leave_type or not start_date or not end_date or not reason:
            return {"error": "Missing required parameters: leave_type, start_date, end_date, reason."}

        allowed_types = {"annual", "sick", "unpaid", "other"}
        if leave_type not in allowed_types:
            return {"error": f"Invalid leave_type '{leave_type}'. Must be one of: {', '.join(sorted(allowed_types))}."}

        leave_type_labels = {
            "annual": "Nghỉ phép năm",
            "sick": "Nghỉ ốm",
            "unpaid": "Nghỉ không lương",
            "other": "Khác",
        }
        leave_label = leave_type_labels.get(leave_type, leave_type)
        preview = f"Xin nghỉ {leave_label} từ {start_date} đến {end_date}. Lý do: {reason}"

        draft = DraftAction(
            action_type="submit_leave_request",
            parameters={"leave_type": leave_type, "start_date": start_date, "end_date": end_date, "reason": reason},
            preview=preview,
            confirm_endpoint="/api/employee-requests/me/leave",
            confirm_method="POST",
            confirm_body={"leave_type": leave_type, "start_date": start_date, "end_date": end_date, "reason": reason},
        )
        return {"draft_action": _draft_to_dict(draft)}

    async def _draft_overtime_request(self, args: dict[str, Any]) -> dict[str, Any]:
        """Draft-Tool: returns a Draft Action for an overtime request."""
        work_date = args.get("work_date")
        start_time = args.get("start_time")
        end_time = args.get("end_time")
        reason = args.get("reason")
        project_or_task = args.get("project_or_task")

        if not work_date or not start_time or not end_time or not reason:
            return {"error": "Missing required parameters: work_date, start_time, end_time, reason."}

        preview = f"Đăng ký tăng ca ngày {work_date}, {start_time} - {end_time}. Lý do: {reason}"
        if project_or_task:
            preview += f" | Dự án: {project_or_task}"

        body: dict[str, Any] = {"work_date": work_date, "start_time": start_time, "end_time": end_time, "reason": reason}
        if project_or_task:
            body["project_or_task"] = project_or_task

        draft = DraftAction(
            action_type="submit_overtime_request",
            parameters={"work_date": work_date, "start_time": start_time, "end_time": end_time, "reason": reason, "project_or_task": project_or_task},
            preview=preview,
            confirm_endpoint="/api/employee-requests/me/overtime",
            confirm_method="POST",
            confirm_body=body,
        )
        return {"draft_action": _draft_to_dict(draft)}

    # -----------------------------------------------------------------------
    # OpenAI-format tools
    # -----------------------------------------------------------------------

    def get_openai_tools(self) -> list[dict]:
        """Convert EMPLOYEE_TOOL_DEFINITIONS to OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in EMPLOYEE_TOOL_DEFINITIONS
        ]


def _draft_to_dict(draft: DraftAction) -> dict[str, Any]:
    """Convert a DraftAction dataclass to a dict for JSON serialization."""
    return {
        "action_type": draft.action_type,
        "parameters": draft.parameters,
        "preview": draft.preview,
        "confirm_endpoint": draft.confirm_endpoint,
        "confirm_method": draft.confirm_method,
        "confirm_body": draft.confirm_body,
    }
