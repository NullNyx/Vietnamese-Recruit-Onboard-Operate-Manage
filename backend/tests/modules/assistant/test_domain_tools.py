"""Test domain tool definitions and OpenAI format conversion."""

from __future__ import annotations

from src.modules.assistant.domain.tools import (
    TOOL_DEFINITIONS,
    ToolKind,
    get_openai_tools,
)


class TestToolDefinitions:
    """Test tool definition structure and correctness."""

    def test_tool_definitions_count(self) -> None:
        """There must be exactly 4 tools."""
        assert len(TOOL_DEFINITIONS) == 4

    def test_all_tools_have_names(self) -> None:
        """Every tool must have a non-empty name."""
        for tool in TOOL_DEFINITIONS:
            assert tool.name, f"Tool missing name"

    def test_all_tools_have_descriptions(self) -> None:
        """Every tool must have a non-empty description."""
        for tool in TOOL_DEFINITIONS:
            assert tool.description, f"Tool '{tool.name}' missing description"

    def test_all_tools_have_parameters(self) -> None:
        """Every tool must have a parameters schema."""
        for tool in TOOL_DEFINITIONS:
            assert tool.parameters, f"Tool '{tool.name}' missing parameters"
            assert tool.parameters.get("type") == "object"

    def test_read_tool_names(self) -> None:
        """Read-Tools have correct names."""
        read_tools = [t for t in TOOL_DEFINITIONS if t.kind == ToolKind.READ]
        names = {t.name for t in read_tools}
        assert "count_candidates_by_status" in names
        assert "list_in_progress_onboarding" in names
        assert "search_candidates" in names

    def test_draft_tool_name(self) -> None:
        """Draft-Tool has correct name."""
        draft_tools = [t for t in TOOL_DEFINITIONS if t.kind == ToolKind.DRAFT]
        assert len(draft_tools) == 1
        assert draft_tools[0].name == "draft_email"


class TestOpenAIFormat:
    """Test OpenAI function-calling format conversion."""

    def test_get_openai_tools_returns_list(self) -> None:
        """get_openai_tools returns a list."""
        result = get_openai_tools()
        assert isinstance(result, list)

    def test_get_openai_tools_count(self) -> None:
        """Returns all 4 tools."""
        result = get_openai_tools()
        assert len(result) == 4

    def test_openai_tool_structure(self) -> None:
        """Each tool has correct OpenAI function-calling structure."""
        for tool in get_openai_tools():
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert func["parameters"]["type"] == "object"

    def test_tool_names_match(self) -> None:
        """OpenAI tool names match TOOL_DEFINITIONS names."""
        openai_names = {t["function"]["name"] for t in get_openai_tools()}
        def_names = {t.name for t in TOOL_DEFINITIONS}
        assert openai_names == def_names


class TestToolFiltering:
    """Test filtering tools by enabled_names parameter."""

    def test_filter_single_tool(self) -> None:
        """Filter to a single tool returns only that tool."""
        result = get_openai_tools(enabled_names={"count_candidates_by_status"})
        assert len(result) == 1
        assert result[0]["function"]["name"] == "count_candidates_by_status"

    def test_filter_multiple_tools(self) -> None:
        """Filter to multiple tools returns only those tools."""
        result = get_openai_tools(
            enabled_names={"count_candidates_by_status", "draft_email"}
        )
        assert len(result) == 2
        names = {t["function"]["name"] for t in result}
        assert names == {"count_candidates_by_status", "draft_email"}

    def test_filter_empty_set(self) -> None:
        """Filter to empty set returns no tools."""
        result = get_openai_tools(enabled_names=set())
        assert len(result) == 0

    def test_filter_unknown_tool_name(self) -> None:
        """Filter with unknown tool name returns no tools."""
        result = get_openai_tools(enabled_names={"nonexistent_tool"})
        assert len(result) == 0

    def test_filter_all_tools(self) -> None:
        """Filter with all tool names returns all tools."""
        all_names = {t.name for t in TOOL_DEFINITIONS}
        result = get_openai_tools(enabled_names=all_names)
        assert len(result) == 4

    def test_none_filter_returns_all(self) -> None:
        """None filter (backwards compatible) returns all tools."""
        result = get_openai_tools(enabled_names=None)
        assert len(result) == 4
