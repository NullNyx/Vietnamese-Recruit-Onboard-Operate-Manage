# 09 — Quality & Feedback

Chat session tracking, user feedback, tool call telemetry.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-chat-session-tracking.md` | Session được tạo, message_count, end_at | Medium |
| 02 | `02-feedback-collection.md` | Thumbs up/down được lưu đúng | Medium |
| 03 | `03-tool-call-telemetry.md` | Tool call events: duration, success, error | Medium |

## Code liên quan

- `backend/src/modules/assistant/infrastructure/quality_models.py`
- `backend/src/modules/assistant/application/assistant_service.py` (`_record_tool_event`)
- `backend/src/modules/assistant/api/router.py` (feedback endpoint)
- `backend/tests/modules/assistant/test_quality_endpoints.py`
