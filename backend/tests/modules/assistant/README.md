# Safety Testing Framework for AI Assistant Tools

This directory contains the **Safety Testing Framework** that every AI Assistant
tool (HR or Employee) must pass before being considered production-safe.

## Architecture

```
BaseToolSafetyTest  (test_base_safety.py)   ← abstract, 4 safety tests
    │
    ├── TestCountCandidatesByStatusSafety    (test_hr_tool_safety.py)
    ├── TestListInProgressOnboardingSafety   (test_hr_tool_safety.py)
    ├── TestSearchCandidatesSafety           (test_hr_tool_safety.py)
    ├── TestGetCandidateParsedCVSafety       (test_hr_tool_safety.py)
    ├── TestListInterviewsForCandidateSafety (test_hr_tool_safety.py)
    ├── TestGetOnboardingTaskDetailsSafety   (test_hr_tool_safety.py)
    ├── TestDraftInterviewInvitationSafety   (test_hr_tool_safety.py)
    ├── TestDraftCongratulationsEmailSafety  (test_hr_tool_safety.py)
    │
    ├── TestGetMyProfileSafety               (test_employee_tool_safety.py)
    ├── TestListMyDocumentsSafety            (test_employee_tool_safety.py)
    ├── TestGetTodayAttendanceSafety         (test_employee_tool_safety.py)
    ├── TestListMyAttendanceRecordsSafety    (test_employee_tool_safety.py)
    ├── TestListMyEmployeeRequestsSafety     (test_employee_tool_safety.py)
    ├── TestGetMyLeaveBalanceSafety          (test_employee_tool_safety.py)
    ├── TestListMyPayslipsSafety             (test_employee_tool_safety.py)
    ├── TestDraftLeaveRequestSafety          (test_employee_tool_safety.py)
    ├── TestDraftOvertimeRequestSafety       (test_employee_tool_safety.py)
```

## The 4 Safety Tests (BaseToolSafetyTest)

Every concrete safety test inherits `BaseToolSafetyTest` and automatically
inherits these 4 tests:

### 1. `test_tool_is_read_only`

**Goal:** Verify the tool handler does NOT call any write method.

**How it works:** Uses `inspect.getsource()` to statically analyze the handler
method's source code. Searches for forbidden patterns:

- `session.commit(`, `session.add(`, `session.flush(`, `session.delete(`
- `.create(`, `.update(`, `.delete(`, `.soft_delete(`, `.upsert(`, `.save(`

This is a **structural** check — it catches violations before the code can ever
execute. No mocking needed.

**Why:** ADR-0006 mandates that the LLM is never given write-capable tools.
All tools are Read-Tool or Draft-Tool only.

### 2. `test_tool_respects_scope`

**Goal:** Verify the tool respects its data scope boundary.

| Assistant Type | Scope Rule |
|---|---|
| **HR Assistant** | Returns **org-wide** data (all candidates, all processes) |
| **Employee Assistant** | Returns **only the authenticated employee's** data (employee_id injected from auth session, never from LLM params) |

Each concrete test implements this by calling the tool and verifying:
- HR tools: Query spans all records (no employee filter)
- Employee tools: Service calls use the injected `employee_id`, not a parameter

**Why:** ADR-0013 mandates Employee Assistant tools are hard-wired to the
authenticated employee. The LLM cannot ask for another employee's data.

### 3. `test_tool_handles_missing_entity`

**Goal:** Verify the tool returns a clear error message (not a crash) when a
referenced entity does not exist.

Applies to tools with entity lookup (e.g., `candidate_id`, `onboarding_process_id`).
Tools without entity lookup set `HAS_ENTITY_LOOKUP = False` and skip this test
or test input validation instead.

**Example:** Passing a valid UUID that doesn't exist in the database must return
`{"error": "Không tìm thấy ứng viên: ..."}` — not a 500 crash.

### 4. `test_tool_handles_invalid_input`

**Goal:** Verify the tool handles malformed input gracefully.

Tests include:
- Invalid UUID strings (`"not-a-uuid"`)
- Missing required parameters
- Out-of-range values (e.g., month 13, year 1800)
- Invalid enum values (e.g., invalid status, invalid leave type)
- Cross-field validation (e.g., end date before start date)

## How to Add Tests for a New Tool

When you add a new tool, follow these steps:

### Step 1: Define the tool (done in `tools.py` or `employee_tools.py`)

Already done — the tool definition includes name, kind, description, and
parameters.

### Step 2: Add the handler (done in `tool_registry.py` or `employee_tool_registry.py`)

Already done — the handler is registered in the `handlers` dict.

### Step 3: Add a safety test class

Create a new test class in `test_hr_tool_safety.py` (for HR tools) or
`test_employee_tool_safety.py` (for employee tools).

**Minimal example — Read-Tool without entity lookup:**

```python
class TestMyNewToolSafety(BaseToolSafetyTest):
    TOOL_NAME = "my_new_tool"
    HANDLER_CLASS = ToolRegistry
    HANDLER_METHOD = "_my_new_tool"
    HAS_ENTITY_LOOKUP = False
    ENTITY_ID_PARAM = None

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        return ToolRegistry(candidate_service=AsyncMock(), onboarding_service=AsyncMock())

    @pytest.fixture
    def valid_args(self) -> dict:
        return {"query": "test"}

    @pytest.mark.asyncio
    async def test_tool_respects_scope(self, registry):
        # Verify org-wide scope
        ...

    @pytest.mark.asyncio
    async def test_tool_handles_missing_entity(self, registry):
        # For tools without entity lookup — test error handling
        ...

    @pytest.mark.asyncio
    async def test_tool_handles_invalid_input(self, registry):
        # Test missing/empty required params
        ...
```

**Minimal example — Read-Tool with entity lookup:**

```python
class TestMyEntityToolSafety(BaseToolSafetyTest):
    TOOL_NAME = "get_my_entity"
    HANDLER_CLASS = ToolRegistry
    HANDLER_METHOD = "_get_my_entity"
    HAS_ENTITY_LOOKUP = True
    ENTITY_ID_PARAM = "entity_id"

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        reg = ToolRegistry(candidate_service=MagicMock(), onboarding_service=AsyncMock())
        reg._candidate_service.get_entity = AsyncMock()
        return reg

    @pytest.fixture
    def valid_args(self) -> dict:
        return {"entity_id": str(uuid4())}

    @pytest.mark.asyncio
    async def test_tool_respects_scope(self, registry):
        ...

    @pytest.mark.asyncio
    async def test_tool_handles_missing_entity(self, registry):
        registry._candidate_service.get_entity = AsyncMock(
            side_effect=Exception("Entity not found")
        )
        result = await self.execute_tool(registry, {
            "entity_id": "00000000-0000-0000-0000-000000000099"
        })
        self.assert_error(result)

    @pytest.mark.asyncio
    async def test_tool_handles_invalid_input(self, registry):
        result = await self.execute_tool(registry, {"entity_id": "bad-uuid"})
        self.assert_error(result)

        result = await self.execute_tool(registry, {})
        self.assert_error(result)
```

### Step 4: Run the tests

```bash
# Run all safety tests
cd backend
python -m pytest tests/modules/assistant/test_base_safety.py -v
python -m pytest tests/modules/assistant/test_hr_tool_safety.py -v
python -m pytest tests/modules/assistant/test_employee_tool_safety.py -v

# Run a single tool's safety tests
python -m pytest tests/modules/assistant/test_hr_tool_safety.py::TestMyNewToolSafety -v
```

## Class Variables Reference

| Variable | Required | Description |
|---|---|---|
| `TOOL_NAME` | **Yes** | Matches `ToolDefinition.name` |
| `HANDLER_CLASS` | **Yes** | Registry class (`ToolRegistry` or `EmployeeToolRegistry`) |
| `HANDLER_METHOD` | **Yes** | Private handler method name (e.g. `"_my_tool"`) |
| `HAS_ENTITY_LOOKUP` | No (default `True`) | Whether tool looks up a DB entity |
| `ENTITY_ID_PARAM` | No (default `None`) | Parameter name for entity ID |
| `NO_PARAMS` | No (default `False`) | Whether tool accepts zero parameters |

## Fixtures to Override

| Fixture | Required | Description |
|---|---|---|
| `registry` | **Yes** | Registry with mocked dependencies |
| `valid_args` | **Yes** | Valid arguments dict for the tool |

## Helper Methods

| Method | Description |
|---|---|
| `execute_tool(registry, args)` | Executes `registry.execute(TOOL_NAME, args)` and returns parsed result |
| `assert_error(result)` | Asserts `result` contains a non-empty `"error"` key |

## Related ADRs

- **ADR-0006:** LLM is never given write-capable tools; human-in-the-loop for
  Draft-Tools.
- **ADR-0013:** Employee Assistant tools are scoped to authenticated employee;
  employee_id is injected from session, never exposed as a parameter.
