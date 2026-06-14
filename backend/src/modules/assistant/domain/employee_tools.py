"""Tool definitions for the Employee Assistant.

Employee Assistant tools are scoped to the authenticated Employee's own data
only. Every Read-Tool filters by the employee_id from the session — the LLM
cannot ask for another employee's data because employee_id is never exposed
as a parameter.

Draft-Tools return a Draft Action — they never write to the database.
The employee reviews the draft; on confirm, the frontend calls the real
write endpoint directly (human-in-the-loop, ADR-0006).

Tool set:
- Read-Tool:    get_my_profile
- Read-Tool:    get_my_attendance
- Read-Tool:    get_my_employee_requests
- Read-Tool:    get_my_payslips
- Draft-Tool:   draft_leave_request
- Draft-Tool:   draft_overtime_request
"""

from __future__ import annotations

from src.modules.assistant.domain.tools import ToolDefinition, ToolKind

# Date regex: YYYY-MM-DD
_DATE_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
# Time regex: HH:MM (24-hour)
_TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"
# Max length for reason field
_REASON_MAX_LENGTH = 2000

EMPLOYEE_TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_my_profile",
        kind=ToolKind.READ,
        description=(
            "Get the current employee's own profile information. "
            "Returns full name, email, phone, date of birth, gender, address, "
            "department, position, employee code, start date, and contract type. "
            "Use when the employee asks about their own profile or personal details."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
    ),
    ToolDefinition(
        name="get_my_attendance",
        kind=ToolKind.READ,
        description=(
            "Get the current employee's attendance records. "
            "Optionally filter by month and year. "
            "Returns check-in and check-out times for each work date. "
            "Use when the employee asks about their attendance, check-in history, "
            "or working days."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "month": {
                    "type": "integer",
                    "description": "Month (1-12). If omitted, returns recent records.",
                    "minimum": 1,
                    "maximum": 12,
                },
                "year": {
                    "type": "integer",
                    "description": "Year (e.g. 2026). If omitted, uses current year.",
                    "minimum": 2020,
                    "maximum": 2099,
                },
            },
        },
    ),
    ToolDefinition(
        name="get_my_employee_requests",
        kind=ToolKind.READ,
        description=(
            "Get the current employee's own requests (leave and overtime). "
            "Optionally filter by request type (leave or overtime). "
            "Returns status, dates, reason, and timestamps. "
            "Use when the employee asks about their leave or overtime requests, "
            "submission history, or request status."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "request_type": {
                    "type": "string",
                    "description": (
                        "Optional filter by request type. "
                        "One of: leave, overtime. If omitted, returns all."
                    ),
                    "enum": ["leave", "overtime"],
                },
            },
        },
    ),
    ToolDefinition(
        name="get_my_payslips",
        kind=ToolKind.READ,
        description=(
            "Get the current employee's own published payslips. "
            "Returns period, gross salary, net salary, and basic salary "
            "for each payslip. "
            "Use when the employee asks about their payslips, salary history, "
            "or payment records."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
    ),
    ToolDefinition(
        name="draft_leave_request",
        kind=ToolKind.DRAFT,
        description=(
            "Draft a leave request for the current employee. Returns a Draft Action "
            "with a preview for the employee to review and confirm. "
            "The employee confirms in the UI; only then is the leave request submitted. "
            "Use when the employee asks to take leave, apply for leave, or submit "
            "a leave request."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "leave_type": {
                    "type": "string",
                    "description": (
                        "Type of leave. One of: annual (nghỉ phép năm), "
                        "sick (nghỉ ốm), unpaid (nghỉ không lương), "
                        "other (khác)."
                    ),
                    "enum": ["annual", "sick", "unpaid", "other"],
                },
                "start_date": {
                    "type": "string",
                    "description": "First day of leave. Format: YYYY-MM-DD.",
                    "pattern": _DATE_PATTERN,
                },
                "end_date": {
                    "type": "string",
                    "description": "Last day of leave. Must be >= start_date. Format: YYYY-MM-DD.",
                    "pattern": _DATE_PATTERN,
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the leave request (max 2000 chars).",
                    "maxLength": _REASON_MAX_LENGTH,
                },
            },
            "required": ["leave_type", "start_date", "end_date", "reason"],
        },
    ),
    ToolDefinition(
        name="draft_overtime_request",
        kind=ToolKind.DRAFT,
        description=(
            "Draft an overtime request for the current employee. Returns a Draft Action "
            "with a preview for the employee to review and confirm. "
            "The employee confirms in the UI; only then is the overtime request submitted. "
            "Use when the employee asks to register overtime, submit overtime, "
            "or log extra hours."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "work_date": {
                    "type": "string",
                    "description": "Date overtime is worked. Format: YYYY-MM-DD.",
                    "pattern": _DATE_PATTERN,
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time. Format: HH:MM (24-hour).",
                    "pattern": _TIME_PATTERN,
                },
                "end_time": {
                    "type": "string",
                    "description": "End time. Must be after start_time. Format: HH:MM (24-hour).",
                    "pattern": _TIME_PATTERN,
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the overtime (max 2000 chars).",
                    "maxLength": _REASON_MAX_LENGTH,
                },
                "project_or_task": {
                    "type": "string",
                    "description": "Optional project or task name (max 255 chars).",
                    "maxLength": 255,
                },
            },
            "required": ["work_date", "start_time", "end_time", "reason"],
        },
    ),
]

EMPLOYEE_TOOL_NAMES: set[str] = {t.name for t in EMPLOYEE_TOOL_DEFINITIONS}
