# 03 — Telemetry Chính Xác, Latest-Event Aggregation

## Mục tiêu
Xác minh telemetry ghi đúng metadata và aggregate theo latest event.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/gmail/application/classification_telemetry.py`
- Alembic migration 067

## Các bước thực hiện

1. **Telemetry sau 1 lần classify**:
   - Email classify thành công lần đầu
   - Expected: event ghi prompt_tokens, completion_tokens, cost, latency

2. **Telemetry sau retry**:
   - Email fail 1 lần, success lần 2
   - Expected: 2 events, nhưng report chỉ lấy event mới nhất

3. **Telemetry không double-count**:
   - Email retry 3 lần → 3 events
   - Expected: metric tổng hợp không coi 3 events = 3 emails

4. **Telemetry giữa các version**:
   - Email được classify bởi version 1, sau đó version 2
   - Expected: mỗi event có version riêng, report theo version

5. **Telemetry không chứa raw content**:
   - Event không có trường chứa email body hoặc prompt text
   - Expected: chỉ có metadata

## Kết quả mong đợi
- Latest-event aggregation
- Không double-count retry
- Versioned telemetry
- Data minimization

## Test files
- `backend/tests/modules/gmail/test_classification_telemetry.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
