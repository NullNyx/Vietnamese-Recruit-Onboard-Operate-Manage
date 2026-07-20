# 04 — Token Usage & Cost Calculation Chính Xác

## Mục tiêu
Xác minh token usage và estimated cost được tính đúng.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/gmail/infrastructure/ai_classifier.py` (token_usage)
- `backend/src/modules/gmail/application/classification_telemetry.py`
- Provider pricing model

## Các bước thực hiện

1. **Token usage từ LLM response**:
   - Gửi 1 email classify → LLM trả về usage {prompt_tokens, completion_tokens, total_tokens}
   - Expected: token_usage được ghi chính xác vào telemetry

2. **Cost calculation**:
   - prompt_tokens = 200, completion_tokens = 10, giá = $0.15/1M input, $0.60/1M output
   - Expected: cost = 200 * 0.15e-6 + 10 * 0.60e-6 ≈ $0.000036

3. **Cost với model khác nhau**:
   - GPT-4o mini vs Gemma vs Cline pricing khác nhau
   - Expected: cost dùng pricing model đúng

4. **Cost aggregation**:
   - 1000 emails trong tháng
   - Expected: tổng cost hiển thị trong dashboard

5. **Streaming response**:
   - Nếu dùng streaming, token usage có được tính đúng?
   - Expected: usage từ stream chunks cộng lại

## Kết quả mong đợi
- Token usage chính xác
- Cost theo model pricing
- Không thất thoát token count

## Test files
- `backend/tests/modules/gmail/test_classification_telemetry.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
