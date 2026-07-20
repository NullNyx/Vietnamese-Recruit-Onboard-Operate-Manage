# 07 — Email Tiếng Việt Edge Cases

## Mục tiêu
Xác minh classifier hoạt động tốt với các biến thể tiếng Việt: không dấu, teencode, địa phương.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/gmail/infrastructure/ai_classifier.py` (system prompt)
- `backend/src/modules/gmail/application/rules_classifier.py`

## Các bước thực hiện

1. **Tiếng Việt không dấu**: "e ten la Nguyen Van A, tot nghiep DH BK TPHCM, e muon ung tuyen vi tri backend"
   - Expected: category = `recruitment`

2. **Teencode/GEN Z**: "a oi e apply job nay dc ko a, e biet React vs Node nhe", "cv e day a link"
   - Expected: vẫn nhận diện intent `job_application`

3. **Tiếng Việt + English lẫn lộn**: "Em apply cho vị trí Senior Frontend nhé, em có 3 năm kinh nghiệm React"
   - Expected: phân loại đúng `recruitment`

4. **Tiếng Việt miền Nam/Trung/Bắc**: 
   - Miền Nam: "Dạ em tên A, em muốn xin vô làm bên mình"
   - Miền Trung: "Em tên B, em muốn xin việc ở công ty"
   - Miền Bắc: "Em tên C, em ứng tuyển vị trí designer ạ"
   - Expected: tất cả đều phân loại đúng

5. **Email dài, lan man**: email 1000 chữ kể chuyện trước khi nói "em muốn ứng tuyển"
   - Expected: vẫn nhận diện intent cuối email

6. **Subject ngắn gọn không dấu**: subject "xiec viec" (xin việc)
   - Expected: keyword matching vẫn bắt được

## Kết quả mong đợi
- Không bỏ sót email tiếng Việt không chuẩn
- Không false negative vì lỗi chính tả/teencode

## Test files
- `backend/tests/modules/gmail/test_classify_integration.py`
- `backend/tests/modules/recruitment/test_intent_classifier.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
