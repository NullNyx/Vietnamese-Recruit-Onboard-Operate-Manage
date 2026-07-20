# 03 — Tool Call Telemetry

## Mục tiêu
Xác minh mỗi lần tool được gọi đều có telemetry record với duration, success, error.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/assistant/infrastructure/quality_models.py` (`AssistantToolCallEvent`)
- `backend/src/modules/assistant/application/assistant_service.py` (`_record_tool_event`)

## Các bước thực hiện

1. **Tool thành công**:
   - LLM gọi count_candidates_by_status → OK
   - Expected: `assistant_tool_call_events` record với:
     - `tool_name` = "count_candidates_by_status"
     - `success` = true
     - `duration_ms` > 0
     - `error_message` = null

2. **Tool thất bại**:
   - LLM gọi search_candidates với query rỗng → error
   - Expected: `success` = false, `error_message` có generic error

3. **Tool call trong 1 session**:
   - 1 session có 5 tool calls
   - Expected: 5 records, cùng `session_id`

4. **Duration chính xác**:
   - Tool chạy ~100ms → `duration_ms` ≈ 100
   - Expected: duration reflect thời gian thực tế

5. **Tool call không session**:
   - Gọi tool từ API test không có session
   - Expected: không crash, nhưng có thể không có event (do session=None)

## Kết quả mong đợi
- Mỗi tool call → 1 event
- Duration, success, error được ghi đúng
- Có thể aggregate để monitoring

## Test files
- `backend/tests/modules/assistant/test_quality_endpoints.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
