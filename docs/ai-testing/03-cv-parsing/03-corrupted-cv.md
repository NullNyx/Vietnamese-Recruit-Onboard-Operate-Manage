# 03 — CV Hỏng / Sai Format

## Mục tiêu
Xác minh hệ thống xử lý graceful khi CV bị hỏng, sai format, hoặc không parse được.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/recruitment/application/intent_classifier.py`
- `backend/src/modules/gmail/application/attachment_service.py`

## Các bước thực hiện

1. **CV PDF corrupted**: file PDF 0 bytes hoặc truncated
   - Expected: lỗi được catch, ghi log, item vào recovery queue

2. **CV sai extension**: file .docx đổi tên thành .pdf
   - Expected: kiểm tra actual MIME type, xử lý đúng

3. **CV quá lớn**: file CV 50MB
   - Expected: từ chối với lý do kích thước, không gửi lên LLM

4. **CV password protected**: PDF có password
   - Expected: trả lỗi rõ ràng, không crash

5. **CV dạng ảnh trong Word**: file .docx chứa toàn ảnh
   - Expected: parse được nếu OCR, hoặc fallback "Không thể đọc text"

6. **Provider lỗi khi parse**: LLM provider unavailable lúc parse
   - Expected: retry với backoff, sau đó fallback manual

## Kết quả mong đợi
- Không crash
- Lỗi được ghi nhận rõ ràng
- CV vào recovery/manual review khi không parse được

## Test files
- `backend/tests/modules/recruitment/test_cv_processor.py`
- `backend/tests/modules/gmail/test_classify_auto_cv_pipeline.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
