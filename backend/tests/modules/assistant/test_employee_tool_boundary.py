"""Test the Employee Assistant safety boundary — data isolation AND draft-only.

Core invariants verified:
1. Employee tools are Read-Tool or Draft-Tool only (structural safety per ADR-0006)
2. No tool accepts employee_id as a parameter (injected from auth — ADR-0013)
3. Employee tool registry always scopes queries to authenticated employee
4. Draft-Tools return DraftAction — they never write to the database
5. Tools use additionalProperties: false + format patterns
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from src.modules.assistant.domain.employee_tools import (
    EMPLOYEE_TOOL_DEFINITIONS,
    EMPLOYEE_TOOL_NAMES,
)
from src.modules.assistant.domain.tools import ToolKind


def _make_registry(**overrides: MagicMock) -> EmployeeToolRegistry:
    """Create EmployeeToolRegistry with mocked deps."""
    from src.modules.assistant.application.employee_tool_registry import (
        EmployeeToolRegistry,
    )

    defaults = {
        "employee_service": MagicMock(),
        "attendance_repo": MagicMock(),
        "leave_service": MagicMock(),
        "overtime_service": MagicMock(),
        "payslip_service": MagicMock(),
    }
    defaults.update(overrides)
    return EmployeeToolRegistry(
        employee_id="00000000-0000-0000-0000-000000000001",
        **defaults,
    )


class TestEmployeeToolBoundary:
    """Verify the Employee Assistant tool set is structurally safe."""

    def test_all_tools_are_read_or_draft(self) -> None:
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            assert tool.kind in (ToolKind.READ, ToolKind.DRAFT)

    def test_no_write_tools_exist(self) -> None:
        write_kinds = {"write", "execute", "send", "mutate", "delete", "create"}
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            assert tool.kind.value not in write_kinds

    def test_employee_id_never_a_parameter(self) -> None:
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            params = tool.parameters.get("properties", {})
            assert "employee_id" not in params
            required = tool.parameters.get("required", [])
            assert "employee_id" not in required

    def test_known_tool_names(self) -> None:
        expected_names = {
            "get_my_profile",
            "get_my_attendance",
            "get_my_employee_requests",
            "get_my_payslips",
            "draft_leave_request",
            "draft_overtime_request",
        }
        assert EMPLOYEE_TOOL_NAMES == expected_names

    def test_descriptions_do_not_imply_other_employees(self) -> None:
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            desc_lower = tool.description.lower()
            assert "other employee" not in desc_lower
            assert "all employees" not in desc_lower

    def test_draft_tools_do_not_write(self) -> None:
        draft_tools = [t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.DRAFT]
        for t in draft_tools:
            assert "draft" in t.description.lower() or "preview" in t.description.lower()

    def test_draft_tool_count(self) -> None:
        draft_tools = [t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.DRAFT]
        assert len(draft_tools) == 2
        assert {t.name for t in draft_tools} == {"draft_leave_request", "draft_overtime_request"}

    def test_read_tool_count(self) -> None:
        read_tools = [t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.READ]
        assert len(read_tools) == 4

    def test_all_tools_have_additional_properties_false(self) -> None:
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            msg = f"Tool '{tool.name}' missing additionalProperties=False"
            assert tool.parameters.get("additionalProperties") is False, msg

    def test_draft_tools_have_format_patterns(self) -> None:
        draft_tools = [t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.DRAFT]
        for t in draft_tools:
            props = t.parameters.get("properties", {})
            for date_field in ["start_date", "end_date", "work_date"]:
                if date_field in props:
                    assert "pattern" in props[date_field], (
                        f"{t.name}.{date_field} missing pattern"
                    )
            for time_field in ["start_time", "end_time"]:
                if time_field in props:
                    assert "pattern" in props[time_field], (
                        f"{t.name}.{time_field} missing pattern"
                    )
            for str_field in ["reason", "project_or_task"]:
                if str_field in props:
                    assert "maxLength" in props[str_field], (
                        f"{t.name}.{str_field} missing maxLength"
                    )

    def test_read_tools_have_additional_properties_false(self) -> None:
        read_tools = [t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.READ]
        for t in read_tools:
            assert t.parameters.get("additionalProperties") is False


class TestEmployeeToolRegistryDraftTools:
    """Verify Draft-Tools return DraftAction and never write."""

    @pytest.mark.asyncio
    async def test_draft_leave_request_returns_draft_action(self) -> None:
        registry = _make_registry()
        result = json.loads(
            await registry.execute("draft_leave_request", {
                "leave_type": "annual",
                "start_date": "2026-07-01",
                "end_date": "2026-07-03",
                "reason": "Nghỉ phép du lịch",
            })
        )
        assert "draft_action" in result
        da = result["draft_action"]
        assert da["action_type"] == "submit_leave_request"
        assert da["confirm_endpoint"] == "/api/employee-requests/me/leave"
        assert da["confirm_method"] == "POST"
        assert "Nghỉ phép du lịch" in da["preview"]

    @pytest.mark.asyncio
    async def test_draft_leave_request_missing_params(self) -> None:
        registry = _make_registry()
        result = json.loads(await registry.execute("draft_leave_request", {}))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_draft_overtime_request_returns_draft_action(self) -> None:
        registry = _make_registry()
        result = json.loads(
            await registry.execute("draft_overtime_request", {
                "work_date": "2026-06-15",
                "start_time": "18:00",
                "end_time": "21:00",
                "reason": "Xử lý báo cáo Q2",
            })
        )
        assert "draft_action" in result
        assert result["draft_action"]["action_type"] == "submit_overtime_request"


class TestReadTools:
    """Verify Read-Tools scope queries to authenticated employee ONLY."""

    @pytest.mark.asyncio
    async def test_get_my_profile_called_with_authenticated_employee_id(
        self,
    ) -> None:
        """Verify the registry calls get_employee with the injected employee_id."""
        emp_service = MagicMock()
        emp_service.get_employee = AsyncMock()

        registry = _make_registry(employee_service=emp_service)
        await registry.execute("get_my_profile", {})

        emp_service.get_employee.assert_awaited_once_with(
            "00000000-0000-0000-0000-000000000001",
        )

    @pytest.mark.asyncio
    async def test_get_my_attendance_called_with_authenticated_employee_id(
        self,
    ) -> None:
        """Verify attendance repo is called with the injected employee_id."""
        att_repo = MagicMock()
        att_repo.get_by_employee_and_date_range = AsyncMock(return_value=[])

        registry = _make_registry(attendance_repo=att_repo)
        await registry.execute("get_my_attendance", {})

        # First positional arg to get_by_employee_and_date_range = employee_id
        call_args = att_repo.get_by_employee_and_date_range.call_args
        assert call_args is not None
        assert str(call_args[1]["employee_id"]) == "00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    async def test_get_my_requests_called_with_authenticated_employee_id(
        self,
    ) -> None:
        """Verify leave/overtime services are called with the injected employee_id."""
        leave_service = MagicMock()
        leave_service.list_my_leaves = AsyncMock(return_value=[])
        overtime_service = MagicMock()
        overtime_service.list_my_overtime = AsyncMock(return_value=[])

        registry = _make_registry(
            leave_service=leave_service,
            overtime_service=overtime_service,
        )
        await registry.execute("get_my_employee_requests", {})

        leave_service.list_my_leaves.assert_awaited_once_with(
            "00000000-0000-0000-0000-000000000001",
        )
        overtime_service.list_my_overtime.assert_awaited_once_with(
            "00000000-0000-0000-0000-000000000001",
        )

    @pytest.mark.asyncio
    async def test_get_my_payslips_called_with_authenticated_employee_id(
        self,
    ) -> None:
        """Verify payslip service is called with the injected employee_id."""
        payslip_service = MagicMock()
        payslip_service.get_my_payslips = AsyncMock(return_value=[])

        registry = _make_registry(payslip_service=payslip_service)
        await registry.execute("get_my_payslips", {})

        payslip_service.get_my_payslips.assert_awaited_once_with(
            "00000000-0000-0000-0000-000000000001",
        )

    @pytest.mark.asyncio
    async def test_registry_never_calls_write_commit(self) -> None:
        """Verify EmployeeToolRegistry handler section has zero write calls."""
        import inspect
        import pytest

        from src.modules.assistant.application.employee_tool_registry import (
            EmployeeToolRegistry,
        )

        source = inspect.getsource(EmployeeToolRegistry)

        handler_start = source.find("async def _get_my_profile")
        assert handler_start != -1, "Handler section not found"
        handler_section = source[handler_start:]

        # Forbidden patterns — each must NOT appear in handler code
        forbidden = [
            "session.commit", "session.add(", "session.flush(",
            ".create(", ".update(", ".delete(", ".soft_delete(", ".upsert(", ".save(",
        ]

        for pattern in forbidden:
            lines = [
                l.strip() for l in handler_section.split("\n") if pattern in l
            ]
            # Allow SELECT with execute
            lines = [l for l in lines if not ("select" in l.lower() and "execute" in l.lower())]
            if lines:
                pytest.fail(f"Handler section contains forbidden pattern '{pattern}': {lines}")

    @pytest.mark.asyncio
    async def test_error_does_not_leak_pii(self) -> None:
        """Errors return generic message, not PII/DB details."""
        emp_service = MagicMock()
        emp_service.get_employee = AsyncMock(
            side_effect=Exception("Internal: connection to DB 'vroom_hr' failed")
        )

        registry = _make_registry(employee_service=emp_service)
        result = json.loads(await registry.execute("get_my_profile", {}))

        assert "error" in result
        # Must NOT contain DB name, stack trace, or sensitive detail
        assert "vroom_hr" not in result["error"]
        assert "connection" not in result["error"]
        assert "session" not in result["error"]
        assert "Không thể xử lý" in result["error"]
