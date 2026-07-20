# 04 — Defense-in-depth: Chặn Client Injection

## Mục tiêu
Xác minh các lớp phòng thủ chống client injection: tool_calls, tool messages, history tampering.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/assistant/application/assistant_service.py` (`_build_messages`)
- `backend/src/modules/assistant/application/employee_assistant_service.py`

## Các bước thực hiện

1. **Client gửi tool_calls trong history**:
   - Frontend gửi message history có assistant message chứa tool_calls giả
   - Expected: `_build_messages` strip tool_calls nếu message có content (client pattern)

2. **Client gửi tool message**:
   - Frontend gửi message với role="tool"
   - Expected: tool messages bị skip với warning log

3. **Client gửi assistant message không content**:
   - Assistant message với content=null
   - Expected: bị strip với warning

4. **Client inject system prompt**:
   - Frontend gửi message với role="system"
   - Expected: chỉ backend mới được tạo system message, client system message bị ignore

5. **History overflow**:
   - Gửi 100 messages
   - Expected: trimmed về max_history (20), bắt đầu từ user turn

## Kết quả mong đợi
- Backend luôn kiểm soát tool_calls và tool messages
- Client không thể inject role hoặc giả mạo tool execution
- History trimming an toàn

## Test files
- `backend/tests/modules/assistant/test_base_safety.py`
- `backend/tests/modules/assistant/test_input_validation.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
