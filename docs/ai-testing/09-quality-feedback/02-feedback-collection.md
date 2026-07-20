# 02 — Feedback Collection: Thumbs Up/Down

## Mục tiêu
Xác minh người dùng có thể gửi feedback (thumbs up/down) cho câu trả lời của Assistant.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/assistant/infrastructure/quality_models.py` (`AssistantFeedbackEvent`)
- `backend/src/modules/assistant/api/router.py`

## Các bước thực hiện

1. **Thumbs up**: 
   - HR click 👍 cho message thứ 2 trong session
   - POST /api/assistant/feedback {session_id, message_index: 1, feedback_type: "up"}
   - Expected: `assistant_feedback_events` có 1 record

2. **Thumbs down**:
   - HR click 👎 + nhập text "Trả lời sai số liệu"
   - POST feedback với `feedback_type: "down"`, `optional_text: "Trả lời sai số liệu"`
   - Expected: record có cả type và text

3. **Feedback sai message_index**:
   - Gửi feedback với message_index = 999
   - Expected: validation error?

4. **Feedback không có session**:
   - Gửi feedback với session_id không tồn tại
   - Expected: 404 hoặc validation error

5. **Nhiều feedback trong 1 session**:
   - 3 thumbs up, 2 thumbs down trong 1 session
   - Expected: 5 records, phân biệt theo message_index

## Kết quả mong đợi
- Feedback được lưu kèm session_id + message_index
- Có optional text
- Validation hợp lệ

## Test files
- `backend/tests/modules/assistant/test_quality_endpoints.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
