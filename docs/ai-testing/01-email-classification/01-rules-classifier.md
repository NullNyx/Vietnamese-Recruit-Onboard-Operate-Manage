# 01 — Rules Classifier Phân Loại Đúng 15 Category

## Mục tiêu
Xác minh rule-based classifier xử lý đúng các email có pattern rõ ràng mà không cần gọi LLM.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/gmail/application/rules_classifier.py`
- `backend/src/modules/gmail/domain/enums.py` (EmailCategory)

## Điều kiện tiên quyết
- Backend đang chạy
- Có Gmail connection đã sync email
- Rules classifier đã được load (CLASSIFICATION_RULES)

## Các bước thực hiện

1. **Gửi email từ domain tuyển dụng** (vietnamworks.com, topcv.vn) với subject "Ứng tuyển vị trí Backend Developer"
   - Expected: category = `recruitment`, confidence ≥ 0.7, source = "rules"

2. **Gửi email với subject "Xin nghỉ phép ngày 20/07"** từ email nội bộ
   - Expected: category = `leave_request`

3. **Gửi email từ "@baohiemxahoi.gov.vn"** về BHXH
   - Expected: category = `insurance`

4. **Gửi email nội bộ** "Báo cáo tháng 7" từ đồng nghiệp
   - Expected: category = `internal`

5. **Gửi email vendor** "Báo giá teambuilding" từ travel agency
   - Expected: category = `vendor`

6. **Gửi email không khớp rule nào**
   - Expected: confidence thấp → fallback sang AI classifier

## Kết quả mong đợi
- Rules classifier xử lý ~60% email, còn lại chuyển AI classifier
- Không false positive (email internal → recruitment)
- Domain Vietnamese job board được nhận diện đúng

## Test files
- `backend/tests/modules/gmail/test_classify_integration.py`
- `backend/tests/modules/gmail/test_classify_preservation.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
