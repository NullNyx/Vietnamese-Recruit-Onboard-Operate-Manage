# 04 — Assistant Trả Lời Đúng Dữ Liệu Live

## Mục tiêu
Xác minh Assistant không trả lời sai, không bịa dữ liệu, dữ liệu là live data.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/assistant/application/assistant_service.py`
- `backend/src/modules/assistant/application/tool_registry.py`

## Các bước thực hiện

1. **Dữ liệu thay đổi giữa các lần hỏi**:
   - Hỏi "Có bao nhiêu candidate?" → nhận X
   - HR thêm 1 candidate mới
   - Hỏi lại → nhận X+1 (live data, không cached)

2. **Assistant không bịa dữ liệu**:
   - Hỏi "Nguyễn Văn Z có kinh nghiệm gì?" (candidate không tồn tại)
   - Expected: trả lời "Không tìm thấy ứng viên", không tự bịa

3. **Assistant không trả lời ngoài scope**:
   - Hỏi "Thời tiết hôm nay thế nào?"
   - Expected: từ chối lịch sự, hoặc nói chỉ hỗ trợ HR

4. **Câu hỏi phức tạp cần context**:
   - "So sánh CV của A và B xem ai phù hợp hơn cho vị trí Backend?"
   - Expected: gọi get_candidate_parsed_cv cho cả 2, so sánh dựa trên skills/experience

5. **Tiếng Việt tự nhiên**:
   - "Tao muốn coi tụi nó phỏng vấn tới đâu rồi?"
   - Expected: hiểu ngữ cảnh, trả lời bằng tiếng Việt

## Kết quả mong đợi
- Dữ liệu luôn là live data
- Không hallucination
- Trả lời đúng ngữ cảnh tiếng Việt

## Test files
- `backend/tests/modules/assistant/test_tool_registry.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
