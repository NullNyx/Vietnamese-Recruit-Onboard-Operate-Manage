# 04 — Provider Fallback: Không Gộp Thành "other"

## Mục tiêu
Xác minh khi provider lỗi, không chuyển category thành `other` hoặc `uncategorized` một cách âm thầm.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/gmail/application/provider_fallback.py`
- `backend/src/modules/gmail/infrastructure/ai_classifier.py`

## Các bước thực hiện

1. **Provider error → fallback**:
   - AI classifier gặp lỗi `APIConnectionError`
   - Expected: email giữ trạng thái `pending_classification`, KHÔNG tự gán `uncategorized`

2. **Provider trả response rỗng**:
   - API trả HTTP 200 nhưng body rỗng
   - Expected: coi như error, retry

3. **Provider trả category không hợp lệ**:
   - LLM hallucinate trả về "spam"
   - Expected: validation, fallback về `uncategorized` (có log warning)

4. **Provider trả format sai**:
   - Response không parse được JSON
   - Expected: retry, sau đó pending

5. **Rules classifier fallback khi AI fail**:
   - AI classifier fail → có fallback về rules classifier không?
   - Expected: nếu rules đã chạy trước AI, giữ kết quả rules với confidence thấp

## Kết quả mong đợi
- Provider error ≠ `other`/`uncategorized`
- Error → pending, không silent misclassification
- Validation category trước khi lưu

## Test files
- `backend/tests/modules/gmail/test_ai_automation_recovery.py`
- `backend/tests/modules/gmail/test_classify_preservation.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
