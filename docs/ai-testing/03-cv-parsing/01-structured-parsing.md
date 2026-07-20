# 01 — Parse CV Đúng Các Field Cấu Trúc

## Mục tiêu
Xác minh CV parser trích xuất đúng và đầy đủ thông tin từ CV tiếng Việt và tiếng Anh.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/recruitment/application/intent_classifier.py`
- `backend/src/modules/recruitment/infrastructure/llm_adapter.py`

## Các bước thực hiện

### CV Tiếng Việt

1. **CV đầy đủ**: CV có đủ: Họ tên, Email, SĐT, Kỹ năng, Kinh nghiệm, Học vấn, Mục tiêu
   - Expected: `parsed_cv_json` chứa tất cả field, `confidence_score` ≥ 0.8

2. **CV thiếu một số field**: CV chỉ có tên, SĐT, kinh nghiệm (không có học vấn)
   - Expected: field thiếu = null/rỗng, field có = parsed đúng

3. **CV tiếng Anh**: CV hoàn toàn tiếng Anh
   - Expected: parse đúng, không bị language barrier

4. **CV dạng ảnh (scan)**: CV dạng PDF scan, cần OCR
   - Expected: parse được nếu có OCR support, hoặc trả lỗi rõ ràng

### Chất lượng Parse

5. **Skills extraction**: CV ghi "Thành thạo: Python, React, Docker, AWS"
   - Expected: `skills` = `["Python", "React", "Docker", "AWS"]`

6. **Experience timeline**: CV ghi "2020-2023: FPT Software, Developer"
   - Expected: `experience` chứa object với company, role, duration

7. **Education**: CV ghi "Đại học Bách Khoa TPHCM, CNTT, 2016-2020"
   - Expected: `education` chứa school, major, year

## Kết quả mong đợi
- `parsed_cv_json` có schema nhất quán
- `confidence_score` phản ánh chất lượng parse
- Không bịa thông tin (hallucination)

## Test files
- `backend/tests/modules/recruitment/test_cv_processor.py`
- `backend/tests/modules/recruitment/test_cv_processor_integration.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
