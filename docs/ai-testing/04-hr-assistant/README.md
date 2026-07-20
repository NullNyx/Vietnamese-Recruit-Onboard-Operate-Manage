# 04 — HR Assistant

Chatbot AI cho HR (role admin): Read-Tools + Draft-Tools + Tool Loop.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-read-tools.md` | 8 Read-Tools trả về dữ liệu chính xác | High |
| 02 | `02-draft-tools.md` | 2 Draft-Tools tạo Draft Action đúng format | High |
| 03 | `03-tool-loop.md` | Tool-calling loop chạy đúng, max 5 iterations | High |
| 04 | `04-wrong-data.md` | Assistant trả lời đúng dữ liệu live, không sai | High |
| 05 | `05-provenance-audit.md` | Provenance và audit decision hoạt động | Medium |

## Code liên quan

- `backend/src/modules/assistant/application/assistant_service.py`
- `backend/src/modules/assistant/application/tool_registry.py`
- `backend/src/modules/assistant/domain/tools.py`
- `backend/src/modules/assistant/api/router.py`
- `frontend/app/(dashboard)/assistant/page.tsx`
- `backend/tests/modules/assistant/test_tool_registry.py`
- `backend/tests/modules/assistant/test_tool_boundary.py`
- `backend/tests/modules/assistant/test_hr_tool_safety.py`
