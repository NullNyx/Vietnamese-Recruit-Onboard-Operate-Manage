# 01 — Chat Session Tracking

## Mục tiêu
Xác minh chat session được tạo, cập nhật message_count, end_at khi kết thúc.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/assistant/infrastructure/quality_models.py` (`AssistantChatSession`)
- `backend/src/modules/assistant/application/assistant_service.py`

## Các bước thực hiện

1. **Tạo session mới**:
   - HR bắt đầu chat → POST /api/assistant/chat
   - Expected: `assistant_chat_sessions` có 1 record với:
     - `user_id` = HR user
     - `assistant_type` = "hr"
     - `start_at` = timestamp
     - `message_count` = 0

2. **Cập nhật message_count**:
   - Gửi 1 message → message_count = 1
   - Gửi 3 messages → message_count = 3
   - Expected: tăng sau mỗi exchange

3. **Kết thúc session**:
   - HR rời trang chat → PUT /api/assistant/chat/{session_id}/end
   - Expected: `end_at` được set, `message_count` = final

4. **Employee session**:
   - Employee sử dụng Employee Assistant
   - Expected: `assistant_type` = "employee", `employee_id` = employee UUID

5. **Session lỗi**:
   - LLM provider lỗi
   - Expected: `last_error` ghi nhận lỗi (generic, không PII)

## Kết quả mong đợi
- Mỗi chat session được track
- Phân biệt HR vs Employee
- Error được ghi nhận

## Test files
- `backend/tests/modules/assistant/test_quality_endpoints.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
