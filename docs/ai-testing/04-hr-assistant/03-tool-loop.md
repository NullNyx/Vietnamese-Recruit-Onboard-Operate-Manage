# 03 — Tool-Calling Loop: Max 5 Iterations, Fallback

## Mục tiêu
Xác minh tool-calling loop chạy đúng, không infinite loop, có fallback khi quá iteration.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/assistant/application/assistant_service.py` (`_MAX_TOOL_ITERATIONS = 5`)

## Các bước thực hiện

1. **Chat bình thường**: "Có bao nhiêu ứng viên?"
   - Expected: LLM gọi count_candidates_by_status (1 iteration) → trả lời text

2. **Chat cần 2 tools**: "Tìm Nguyễn Văn A rồi cho tôi xem CV"
   - Expected: iteration 1: search_candidates → iteration 2: get_candidate_parsed_cv → text

3. **Chat cần 3 tools**: "Tìm các vị trí open, xem phòng ban, rồi đếm candidate"
   - Expected: 3 iterations, sau đó text response

4. **LLM gọi tool liên tục**: giả lập LLM luôn trả về tool_calls
   - Expected: sau 5 iterations → fallback text: "Xin lỗi, trợ lý đã xử lý quá nhiều bước..."

5. **LLM không trả text ở cuối**: chỉ toàn tool_calls
   - Expected: fallback text xuất hiện (diagnosis #3)

6. **History trimming**: chat 30 messages → gửi LLM ≤ 20 messages gần nhất
   - Expected: context không bị overflow, assistant vẫn trả lời đúng

## Kết quả mong đợi
- Loop dừng sau tối đa 5 iterations
- Có fallback text khi hết loop không có câu trả lời
- History trimming hoạt động

## Test files
- `backend/tests/modules/assistant/test_tool_loop_fallback.py`
- `backend/tests/modules/assistant/test_tool_boundary.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
