"""Test the Employee Assistant safety boundary — data isolation AND draft-only.

Core invariants verified:
1. Employee tools are Read-Tool or Draft-Tool only (structural safety per ADR-0006)
2. No tool accepts employee_id as a parameter (injected from auth — ADR-0013)
3. Employee tool registry always scopes queries to authenticated employee
4. Draft-Tools return DraftAction — they never write to the database
5. Draft-Tools do NOT accept employee_id as a parameter
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.modules.assistant.domain.employee_tools import (
    EMPLOYEE_TOOL_DEFINITIONS,
    EMPLOYEE_TOOL_NAMES,
)
from src.modules.assistant.domain.tools import ToolKind


def _make_registry() -> EmployeeToolRegistry:
    """Create EmployeeToolRegistry with mocked deps for tool-level tests."""
    from src.modules.assistant.application.employee_tool_registry import (
        EmployeeToolRegistry,
    )

    return EmployeeToolRegistry(
        employee_id="00000000-0000-0000-0000-000000000001",  # type: ignore
        employee_service=MagicMock(),
        attendance_repo=MagicMock(),
        leave_service=MagicMock(),
        overtime_service=MagicMock(),
        payslip_service=MagicMock(),
    )


class TestEmployeeToolBoundary:
    """Verify the Employee Assistant tool set is structurally safe."""

    def test_all_tools_are_read_or_draft(self) -> None:
        """Every employee tool must be Read-Tool or Draft-Tool — no write tools."""
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            assert tool.kind in (ToolKind.READ, ToolKind.DRAFT), (
                f"Employee tool '{tool.name}' has unexpected kind '{tool.kind}'. "
                f"Only 'read' and 'draft' are allowed (ADR-0006)."
            )

    def test_no_write_tools_exist(self) -> None:
        """No employee tool with write kind exists."""
        write_kinds = {"write", "execute", "send", "mutate", "delete", "create"}
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            assert tool.kind.value not in write_kinds, (
                f"Employee tool '{tool.name}' has write-capable kind "
                f"'{tool.kind}'. This violates ADR-0006."
            )

    def test_employee_id_never_a_parameter(self) -> None:
        """employee_id must NEVER be a param in any tool (read OR draft).

        This is the structural guarantee that the Employee Assistant can only
        read the authenticated employee's own data (ADR-0013).
        """
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            params = tool.parameters.get("properties", {})
            assert "employee_id" not in params, (
                f"Employee tool '{tool.name}' accepts employee_id as a parameter. "
                f"This violates ADR-0013: employee_id must be injected from auth."
            )
            required = tool.parameters.get("required", [])
            assert "employee_id" not in required, (
                f"Employee tool '{tool.name}' has employee_id as a required param. "
                f"This violates ADR-0013."
            )

    def test_known_tool_names(self) -> None:
        """Verify current employee tool set is as expected (4 read + 2 draft)."""
        expected_names = {
            "get_my_profile",
            "get_my_attendance",
            "get_my_employee_requests",
            "get_my_payslips",
            "draft_leave_request",
            "draft_overtime_request",
        }
        assert EMPLOYEE_TOOL_NAMES == expected_names, (
            f"Employee tool set mismatch. Expected {expected_names}, "
            f"got {EMPLOYEE_TOOL_NAMES}."
        )

    def test_descriptions_do_not_imply_other_employees(self) -> None:
        """Tool descriptions must not hint at accessing other employees' data."""
        for tool in EMPLOYEE_TOOL_DEFINITIONS:
            desc_lower = tool.description.lower()
            assert "other employee" not in desc_lower
            assert "all employees" not in desc_lower

    def test_draft_tools_do_not_write(self) -> None:
        """Draft-Tools must indicate they only draft/propose, not execute."""
        draft_tools = [
            t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.DRAFT
        ]
        for t in draft_tools:
            desc_lower = t.description.lower()
            assert "draft" in desc_lower or "preview" in desc_lower

    def test_draft_tool_count(self) -> None:
        """There should be exactly 2 Draft-Tools."""
        draft_tools = [
            t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.DRAFT
        ]
        assert len(draft_tools) == 2
        names = {t.name for t in draft_tools}
        assert names == {"draft_leave_request", "draft_overtime_request"}

    def test_read_tool_count(self) -> None:
        """There should be exactly 4 Read-Tools."""
        read_tools = [
            t for t in EMPLOYEE_TOOL_DEFINITIONS if t.kind == ToolKind.READ
        ]
        assert len(read_tools) == 4
        read_names = {t.name for t in read_tools}
        assert read_names == {
            "get_my_profile",
            "get_my_attendance",
            "get_my_employee_requests",
            "get_my_payslips",
        }


class TestEmployeeToolRegistryDraftTools:
    """Verify Draft-Tools return DraftAction and never write."""

    @pytest.mark.asyncio
    async def test_draft_leave_request_returns_draft_action(self) -> None:
        """draft_leave_request returns a DraftAction with correct structure."""
        registry = _make_registry()
        result = json.loads(
            await registry.execute(
                "draft_leave_request",
                {
                    "leave_type": "annual",
                    "start_date": "2026-07-01",
                    "end_date": "2026-07-03",
                    "reason": "Nghỉ phép du lịch",
                },
            )
        )

        assert "draft_action" in result
        da = result["draft_action"]
        assert da["action_type"] == "submit_leave_request"
        assert da["confirm_endpoint"] == "/api/employee-requests/me/leave"
        assert da["confirm_method"] == "POST"
        assert da["preview"]
        assert "2026-07-01" in da["preview"]
        assert "Nghỉ phép du lịch" in da["preview"]
        assert da["confirm_body"]["leave_type"] == "annual"

    @pytest.mark.asyncio
    async def test_draft_leave_request_missing_params(self) -> None:
        """draft_leave_request returns error when params are missing."""
        registry = _make_registry()
        result = json.loads(
            await registry.execute("draft_leave_request", {"leave_type": "annual"})
        )
        assert "error" in result
        assert "Missing required parameters" in result["error"]

    @pytest.mark.asyncio
    async def test_draft_leave_request_invalid_leave_type(self) -> None:
        """draft_leave_request returns error for invalid leave_type."""
        registry = _make_registry()
        result = json.loads(
            await registry.execute(
                "draft_leave_request",
                {
                    "leave_type": "invalid_type",
                    "start_date": "2026-07-01",
                    "end_date": "2026-07-03",
                    "reason": "test",
                },
            )
        )
        assert "error" in result
        assert "Invalid leave_type" in result["error"]

    @pytest.mark.asyncio
    async def test_draft_overtime_request_returns_draft_action(self) -> None:
        """draft_overtime_request returns a DraftAction with correct structure."""
        registry = _make_registry()
        result = json.loads(
            await registry.execute(
                "draft_overtime_request",
                {
                    "work_date": "2026-06-15",
                    "start_time": "18:00",
                    "end_time": "21:00",
                    "reason": "Xử lý báo cáo tháng",
                    "project_or_task": "Báo cáo Q2",
                },
            )
        )
        assert "draft_action" in result
        da = result["draft_action"]
        assert da["action_type"] == "submit_overtime_request"
        assert da["confirm_endpoint"] == "/api/employee-requests/me/overtime"
        assert da["confirm_method"] == "POST"
        assert "18:00" in da["preview"]
        assert "Báo cáo Q2" in da["preview"]

    @pytest.mark.asyncio
    async def test_draft_overtime_request_missing_params(self) -> None:
        """draft_overtime_request returns error when params are missing."""
        registry = _make_registry()
        result = json.loads(
            await registry.execute(
                "draft_overtime_request", {"work_date": "2026-06-15"}
            )
        )
        assert "error" in result
        assert "Missing required parameters" in result["error"]

    @pytest.mark.asyncio
    async def test_draft_overtime_request_optional_project(self) -> None:
        """draft_overtime_request works without optional project_or_task."""
        registry = _make_registry()
        result = json.loads(
            await registry.execute(
                "draft_overtime_request",
                {
                    "work_date": "2026-06-15",
                    "start_time": "18:00",
                    "end_time": "20:00",
                    "reason": "Làm bù",
                },
            )
        )
        assert "draft_action" in result
        da = result["draft_action"]
        assert "project_or_task" not in da["confirm_body"]

    @pytest.mark.asyncio
    async def test_draft_tool_marked_as_draft(self) -> None:
        """is_draft_tool returns True for draft tools, False for read tools."""
        registry = _make_registry()
        assert registry.is_draft_tool("draft_leave_request")
        assert registry.is_draft_tool("draft_overtime_request")
        assert not registry.is_draft_tool("get_my_profile")

    @pytest.mark.asyncio
    async def test_tool_registry_rejects_unknown_tool(self) -> None:
        """Registry returns error for unknown tool names."""
        registry = _make_registry()
        result = json.loads(await registry.execute("nonexistent_tool", {}))
        assert "error" in result
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_read_tool_returns_data_not_draft_action(self) -> None:
        """Read-Tool execution returns data, never a draft_action."""
        # get_my_profile with mocked employee_service
        from unittest.mock import AsyncMock

        mock_employee = MagicMock()
        mock_employee.employee_code = "NV-001"
        mock_employee.full_name = "Test"
        mock_employee.email = "test@co.com"
        mock_employee.phone = None
        mock_employee.date_of_birth = None
        mock_employee.gender = None
        mock_employee.address = None
        mock_employee.department_id = None
        mock_employee.position_id = None
        mock_employee.start_date = None
        mock_employee.contract_type = None

        emp_service = MagicMock()
        emp_service.get_employee = AsyncMock(return_value=mock_employee)

        from src.modules.assistant.application.employee_tool_registry import (
            EmployeeToolRegistry,
        )

        registry = EmployeeToolRegistry(
            employee_id="00000000-0000-0000-0000-000000000001",  # type: ignore
            employee_service=emp_service,
            attendance_repo=MagicMock(),
            leave_service=MagicMock(),
            overtime_service=MagicMock(),
            payslip_service=MagicMock(),
        )

        result = json.loads(await registry.execute("get_my_profile", {}))
        assert "draft_action" not in result
        assert result["full_name"] == "Test"
        assert result["employee_code"] == "NV-001"


class TestReadTools:
    """Verify Read-Tools return data (not draft_action)."""

    @pytest.mark.asyncio
    async def test_get_my_attendance_returns_data(self) -> None:
        """get_my_attendance returns records, filtered by employee."""
        from unittest.mock import AsyncMock

        from datetime import date
        from src.modules.assistant.application.employee_tool_registry import (
            EmployeeToolRegistry,
        )

        mock_record = MagicMock()
        mock_record.work_date = date(2026, 6, 15)
        mock_record.check_in_at = None
        mock_record.check_out_at = None
        mock_record.source = None

        att_repo = MagicMock()
        att_repo.get_by_employee_and_date_range = AsyncMock(return_value=[mock_record])

        registry = EmployeeToolRegistry(
            employee_id="00000000-0000-0000-0000-000000000001",  # type: ignore
            employee_service=MagicMock(),
            attendance_repo=att_repo,
            leave_service=MagicMock(),
            overtime_service=MagicMock(),
            payslip_service=MagicMock(),
        )

        result = json.loads(await registry.execute("get_my_attendance", {}))
        assert "records" in result
        assert len(result["records"]) == 1

    @pytest.mark.asyncio
    async def test_get_my_employee_requests_returns_data(self) -> None:
        """get_my_employee_requests returns requests, scoped to employee."""
        from unittest.mock import AsyncMock

        from src.modules.assistant.application.employee_tool_registry import (
            EmployeeToolRegistry,
        )

        leave_service = MagicMock()
        leave_service.list_my_leaves = AsyncMock(return_value=[])

        overtime_service = MagicMock()
        overtime_service.list_my_overtime = AsyncMock(return_value=[])

        registry = EmployeeToolRegistry(
            employee_id="00000000-0000-0000-0000-000000000001",  # type: ignore
            employee_service=MagicMock(),
            attendance_repo=MagicMock(),
            leave_service=leave_service,
            overtime_service=overtime_service,
            payslip_service=MagicMock(),
        )

        result = json.loads(
            await registry.execute("get_my_employee_requests", {})
        )
        assert "requests" in result
        assert isinstance(result["requests"], list)

    @pytest.mark.asyncio
    async def test_get_my_payslips_returns_data(self) -> None:
        """get_my_payslips returns payslips, scoped to employee."""
        from unittest.mock import AsyncMock

        from src.modules.assistant.application.employee_tool_registry import (
            EmployeeToolRegistry,
        )

        mock_payslip = MagicMock()
        mock_payslip.id = "p1"
        mock_payslip.period_start = None
        mock_payslip.period_end = None
        mock_payslip.gross_salary = 15000000
        mock_payslip.net_salary = 12000000
        mock_payslip.basic_salary = 15000000
        mock_payslip.status = "published"

        payslip_service = MagicMock()
        payslip_service.get_my_payslips = AsyncMock(return_value=[mock_payslip])

        registry = EmployeeToolRegistry(
            employee_id="00000000-0000-0000-0000-000000000001",  # type: ignore
            employee_service=MagicMock(),
            attendance_repo=MagicMock(),
            leave_service=MagicMock(),
            overtime_service=MagicMock(),
            payslip_service=payslip_service,
        )

        result = json.loads(await registry.execute("get_my_payslips", {}))
        assert "payslips" in result
        assert len(result["payslips"]) == 1
