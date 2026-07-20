# 06 — Safety & Security

Ranh giới an toàn cấu trúc: Read-Tool/Draft-Tool, Human-in-the-loop, PII, Defense-in-depth.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-tool-boundary.md` | Chỉ Read + Draft tool, không Write tool | Critical |
| 02 | `02-human-in-the-loop.md` | HR/Employee phải confirm trước khi write | Critical |
| 03 | `03-pii-redaction.md` | Không leak PII vào log/audit/LLM | High |
| 04 | `04-defense-in-depth.md` | Client không inject tool_calls, tool messages | Medium |

## Code liên quan

- `backend/src/modules/assistant/domain/tools.py` (ToolKind)
- `backend/src/modules/assistant/application/assistant_service.py` (_build_messages)
- `backend/src/modules/assistant/application/employee_tool_registry.py`
- `backend/tests/modules/assistant/test_base_safety.py`
- `backend/tests/modules/assistant/test_hr_tool_safety.py`
- `backend/tests/modules/assistant/test_employee_tool_safety.py`
