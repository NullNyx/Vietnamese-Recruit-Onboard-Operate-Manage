# 05 — Employee Assistant

Chatbot AI cho Employee Self-Service: scope chỉ trong dữ liệu của chính employee.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-self-service-read.md` | 7 Read-Tools trả về đúng dữ liệu của employee | High |
| 02 | `02-scope-boundary.md` | Không thể truy cập dữ liệu employee khác | Critical |
| 03 | `03-draft-leave-overtime.md` | Draft-Tools tạo đơn nghỉ phép/tăng ca đúng | High |
| 04 | `04-employee-id-injection.md` | employee_id từ session, LLM không thể inject | Critical |

## Code liên quan

- `backend/src/modules/assistant/domain/employee_tools.py`
- `backend/src/modules/assistant/application/employee_tool_registry.py`
- `backend/src/modules/assistant/application/employee_assistant_service.py`
- `backend/src/modules/assistant/api/employee_router.py`
- `frontend/app/(employee)/employee/assistant/page.tsx`
- `backend/tests/modules/assistant/test_employee_tool_boundary.py`
- `backend/tests/modules/assistant/test_employee_tool_safety.py`
- `backend/tests/modules/assistant/test_employee_no_write.py`
