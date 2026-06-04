"""Tool definitions for the AI Assistant.

Defines the 4 tools available to the LLM:
- Read-Tool: count_candidates_by_status
- Read-Tool: list_in_progress_onboarding
- Read-Tool: search_candidates
- Draft-Tool: draft_email

The LLM is NEVER given a tool that writes to the database (ADR-0006).
Backend executes tools directly — LLM only defines what to call.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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
    parameters: dict


@dataclass(frozen=True)
class DraftAction:
    """Structured proposal returned by a Draft-Tool (CONTEXT.md).

    HR reviews it; on confirm, the frontend calls the real write endpoint
    directly — never the LLM. This is the human-in-the-loop mechanism.

    Attributes:
        action_type: The type of action (e.g. "send_email").
        parameters: Action parameters for the confirm endpoint.
        preview: Human-readable preview for HR.
        confirm_endpoint: The real API endpoint to call on confirm.
        confirm_method: HTTP method for the confirm endpoint.
        confirm_body: The request body for the confirm endpoint.
    """

    action_type: str
    parameters: dict
    preview: str
    confirm_endpoint: str
    confirm_method: str
    confirm_body: dict


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
        name="list_in_progress_onboarding",
        kind=ToolKind.READ,
        description=(
            "List onboarding processes that are currently in progress. "
            "Returns a list of processes with employee name, progress "
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
        name="draft_email",
        kind=ToolKind.DRAFT,
        description=(
            "Draft an email to send to a recipient. Returns a Draft Action "
            "with the email content for HR to review and confirm. "
            "The email is NOT sent until HR confirms. "
            "Use when the user asks to compose, draft, or send an email "
            "to a candidate or any recipient."
        ),
        parameters={
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of recipient email addresses.",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line.",
                },
                "body_html": {
                    "type": "string",
                    "description": "HTML body content of the email.",
                },
            },
            "required": ["to", "subject", "body_html"],
        },
    ),
]


def get_openai_tools(enabled_names: set[str] | None = None) -> list[dict]:
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
