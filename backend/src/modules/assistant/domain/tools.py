"""Tool definitions for the AI Assistant.

Defines the 4 tools available to the LLM:
- Read-Tool: count_candidates_by_status
- Read-Tool: list_in_progress_onboarding
- Read-Tool: search_candidates
- Draft-Tool: draft_interview_invitation
- Draft-Tool: draft_congratulations_email

The LLM is NEVER given a tool that writes to the database (ADR-0006).
Backend executes tools directly — LLM only defines what to call.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ToolKind(StrEnum):
    """Two kinds of tools, and no others (CONTEXT.md)."""

    READ = "read"
    DRAFT = "draft"


@dataclass(frozen=True)
class ToolDefinition:
    """A tool the LLM can invoke.

    Attributes:
        name: Machine-readable tool name.
        kind: Read-Tool or Draft-Tool.
        description: Human-readable description for the LLM.
        parameters: JSON Schema for the tool's parameters.
    """

    name: str
    kind: ToolKind
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class DraftAction:
    """Structured proposal returned by a Draft-Tool (CONTEXT.md).

    HR reviews it; on confirm, the frontend calls the real write endpoint
    directly — never the LLM. This is the human-in-the-loop mechanism.

    Action attributes (from HR’s perspective):
        action_type: What the action is (e.g. send_email).
        parameters: Action parameters.
        preview: Human-readable preview for HR to review.
        confirm_endpoint: The real API endpoint to call on confirm.
        confirm_method: HTTP method for the confirm endpoint.
        confirm_body: The request body for the confirm endpoint.
    """

    action_type: str
    parameters: dict[str, Any]
    preview: str
    provenance: dict[str, Any]
    confirm_endpoint: str
    confirm_method: str
    confirm_body: dict[str, Any]


# ---------------------------------------------------------------------------
# Tool definitions — hardcode per grill decision (System Prompt = static)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="count_candidates_by_status",
        kind=ToolKind.READ,
        description=(
            "Count candidates in the recruitment pipeline, optionally filtered "
            "by status. Returns a list of {status, count} objects. "
            "Use when the user asks how many candidates exist, how many are in "
            "a specific status, or wants a pipeline overview."
        ),
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": (
                        "Optional status filter. One of: new, reviewing, "
                        "interview_scheduled, accepted, rejected, archived. "
                        "If omitted, returns counts for ALL statuses."
                    ),
                },
            },
        },
    ),
    ToolDefinition(
        name="list_interviews_for_candidate",
        kind=ToolKind.READ,
        description=(
            "List interviews for a candidate. Returns a list of interviews with "
            "scheduled_time, status (scheduled/completed/cancelled), location, "
            "and notes. Use when the user asks about a candidate's interview "
            "schedule, upcoming interviews, or interview history."
        ),
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "UUID of the candidate whose interviews to list.",
                },
            },
            "required": ["candidate_id"],
        },
    ),
    ToolDefinition(
        name="get_onboarding_task_details",
        kind=ToolKind.READ,
        description=(
            "Get task details for an onboarding process. Returns a list of tasks "
            "with name, status (pending/done), due_date (if available), "
            "is_overdue (boolean), and assigned_to (if available). "
            "Use when the user asks about onboarding progress, task checklist, "
            "or what remains to be done for a specific onboarding process."
        ),
        parameters={
            "type": "object",
            "properties": {
                "onboarding_process_id": {
                    "type": "string",
                    "description": "UUID of the onboarding process whose tasks to retrieve.",
                },
            },
            "required": ["onboarding_process_id"],
        },
    ),
    ToolDefinition(
        name="list_in_progress_onboarding",
        kind=ToolKind.READ,
        description=(
            "List onboarding processes that are currently in progress. "
            "Returns a list of processes with employee full name, email, progress "
            "(completed/total tasks), and status. "
            "Use when the user asks about onboarding status, who is "
            "being onboarded, or onboarding progress."
        ),
        parameters={
            "type": "object",
            "properties": {},
        },
    ),
        ToolDefinition(
            name="search_candidates",
            kind=ToolKind.READ,
            description=(
                "Search for candidates by name or email. Returns matching "
                "candidates with id, name, email, and status. "
                "Use when the user mentions a specific candidate by name "
                "or email, or before drafting an email to a candidate."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term — matches against candidate name or email.",
                    },
                },
                "required": ["query"],
            },
        ),
        ToolDefinition(
            name="get_candidate_parsed_cv",
            kind=ToolKind.READ,
            description=(
                "Get the parsed CV data for a candidate. Returns structured data "
                "including skills, experience, education, summary, and the full "
                "parsed CV JSON from the AI Automation pipeline. "
                "Use when the user asks about a candidate's CV content, skills, "
                "experience, or background — or before drafting an email to "
                "personalize it with CV details."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "candidate_id": {
                        "type": "string",
                        "description": "UUID of the candidate whose CV to read.",
                    },
                },
                "required": ["candidate_id"],
            },
        ),
        ToolDefinition(
            name="draft_interview_invitation",
        kind=ToolKind.DRAFT,
        description=(
            "Draft an interview invitation email for a candidate. Returns a Draft Action "
            "with the email content for HR to review and confirm. "
            "Use when the user asks to compose or send an interview invitation."
        ),
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "UUID of the candidate.",
                },
                "interview_date": {
                    "type": "string",
                    "description": "Date of the interview (e.g. 15/06/2026 or YYYY-MM-DD).",
                },
                "interview_time": {
                    "type": "string",
                    "description": "Time of the interview (e.g. 09:00 AM).",
                },
                "location": {
                    "type": "string",
                    "description": "Location or Google Meet link for the interview.",
                },
            },
            "required": ["candidate_id", "interview_date", "interview_time", "location"],
        },
        ),
        ToolDefinition(
            name="list_job_openings",
            kind=ToolKind.READ,
            description=(
                "List job openings in the recruitment pipeline, optionally filtered "
                "by status. Returns a list of job openings with id, title, department, "
                "position, headcount_target, headcount_filled, and status. "
                "Use when the user asks about job openings, hiring plans, "
                "or headcount status."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": (
                            "Optional status filter. One of: draft, open, closed, cancelled. "
                            "Defaults to 'open' if omitted."
                        ),
                    },
                },
            },
        ),
        ToolDefinition(
            name="get_department_info",
            kind=ToolKind.READ,
            description=(
                "Get department information. Returns department name, description, "
                "list of positions (title, employee count), and manager info. "
                "If department_id is omitted, returns info for ALL departments. "
                "Use when the user asks about a department's structure, "
                "positions, or management."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "department_id": {
                        "type": "string",
                        "description": (
                            "Optional UUID of the department. If omitted, "
                            "returns info for all departments."
                        ),
                    },
                },
            },
        ),
        ToolDefinition(
            name="draft_congratulations_email",
            kind=ToolKind.DRAFT,
        description=(
            "Draft a congratulations / offer email for a candidate. Returns a Draft Action "
            "with the email content for HR to review and confirm. "
            "Use when the user asks to send an offer or congratulations to a candidate."
        ),
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "UUID of the candidate.",
                },
                "position": {
                    "type": "string",
                    "description": "The job position being offered.",
                },
                "start_date": {
                    "type": "string",
                    "description": "The expected start date (e.g. 15/06/2026 or YYYY-MM-DD).",
                },
            },
            "required": ["candidate_id", "position", "start_date"],
        },
    ),
]


def get_openai_tools(enabled_names: set[str] | None = None) -> list[dict[str, Any]]:
    """Convert TOOL_DEFINITIONS to OpenAI function-calling format.

    Args:
        enabled_names: If provided, only include tools whose name is in this set.
            If None, all tools are included (backwards compatible).

    Returns:
        List of tool dicts in the format expected by the chat completions API.
    """
    tools = TOOL_DEFINITIONS
    if enabled_names is not None:
        tools = [t for t in TOOL_DEFINITIONS if t.name in enabled_names]

    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]
