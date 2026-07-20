# 02 — Email Không Có CV: Không Parse

## Mục tiêu
Xác minh hệ thống không cố gắng parse CV khi email không có attachment hoặc link CV.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/recruitment/application/intent_classifier.py`

## Các bước thực hiện

1. **Email ứng tuyển không CV**: "Em muốn ứng tuyển, em sẽ gửi CV sau"
   - Expected: intent = `job_application`, nhưng không trigger CV parsing

2. **Email ứng tuyển + link CV**: "CV của em: https://topcv.vn/..."
   - Expected: trigger CV parsing từ link (nếu hỗ trợ)

3. **Email có attachment không phải CV**: đính kèm file .docx portfolio
   - Expected: kiểm tra MIME type, nếu là CV-supported thì parse, nếu không thì skip

4. **Email spam attachment**: file .exe, .zip
   - Expected: KHÔNG parse, KHÔNG crash

## Kết quả mong đợi
- Chỉ parse khi có evidence đủ mạnh về CV
- Không crash với attachment lạ

## Test files
- `backend/tests/modules/recruitment/test_cv_processor.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
