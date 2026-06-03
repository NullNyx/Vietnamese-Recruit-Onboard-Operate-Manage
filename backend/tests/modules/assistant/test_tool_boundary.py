"""Test that the AI Assistant has NO write-capable tools.

This is the core safety invariant (ADR-0006, CONTEXT.md):
"The LLM is never given a tool that writes to the database —
that safety boundary is structural, not a convention."

These tests verify that:
1. All defined tools are either Read-Tool or Draft-Tool
2. No tool has write capabilities
3. The OpenAI tool definitions sent to the LLM contain no write operations
"""

from __future__ import annotations

import pytest

from src.modules.assistant.domain.tools import (
    TOOL_DEFINITIONS,
    ToolKind,
    get_openai_tools,
)


class TestToolBoundary:
    """Verify the assistant's tool boundary is structurally safe."""

    def test_all_tools_are_read_or_draft(self) -> None:
        """Every tool must be Read-Tool or Draft-Tool — nothing else."""
        for tool in TOOL_DEFINITIONS:
            assert tool.kind in (ToolKind.READ, ToolKind.DRAFT), (
                f"Tool '{tool.name}' has unexpected kind '{tool.kind}'. "
                f"Only 'read' and 'draft' are allowed (ADR-0006)."
            )

    def test_no_write_tools_exist(self) -> None:
        """No tool with write/write/execute/send kind exists."""
        write_kinds = {"write", "execute", "send", "mutate", "delete", "create"}
        for tool in TOOL_DEFINITIONS:
            assert tool.kind.value not in write_kinds, (
                f"Tool '{tool.name}' has write-capable kind '{tool.kind}'. "
                f"This violates ADR-0006 (structural safety boundary)."
            )

    def test_known_tool_names(self) -> None:
        """Verify exactly the 4 expected tools exist."""
        expected_names = {
            "count_candidates_by_status",
            "list_in_progress_onboarding",
            "search_candidates",
            "draft_email",
        }
        actual_names = {t.name for t in TOOL_DEFINITIONS}
        assert actual_names == expected_names, (
            f"Tool set mismatch. Expected {expected_names}, got {actual_names}. "
            f"Any new tool must be reviewed for write-safety."
        )

    def test_openai_tools_format_has_no_write(self) -> None:
        """The OpenAI-format tool definitions must not contain write operations."""
        openai_tools = get_openai_tools()
        assert len(openai_tools) == 4

        for tool in openai_tools:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

            # Descriptions must not indicate write capability
            desc_lower = func["description"].lower()
            assert "write" not in desc_lower or "never write" in desc_lower, (
                f"Tool '{func['name']}' description may imply write capability: "
                f"{func['description']}"
            )

    def test_draft_email_does_not_execute(self) -> None:
        """The draft_email tool must be Draft-Tool, not execute any write."""
        draft_tool = next(t for t in TOOL_DEFINITIONS if t.name == "draft_email")
        assert draft_tool.kind == ToolKind.DRAFT
        assert "NOT execute" in draft_tool.description or "not" in draft_tool.description.lower()

    def test_draft_tool_count(self) -> None:
        """There should be exactly 1 Draft-Tool (draft_email)."""
        draft_tools = [t for t in TOOL_DEFINITIONS if t.kind == ToolKind.DRAFT]
        assert len(draft_tools) == 1
        assert draft_tools[0].name == "draft_email"

    def test_read_tool_count(self) -> None:
        """There should be exactly 3 Read-Tools."""
        read_tools = [t for t in TOOL_DEFINITIONS if t.kind == ToolKind.READ]
        assert len(read_tools) == 3
        read_names = {t.name for t in read_tools}
        assert read_names == {
            "count_candidates_by_status",
            "list_in_progress_onboarding",
            "search_candidates",
        }
