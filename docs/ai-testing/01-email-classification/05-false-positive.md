# 05 — Không False Positive: Email Nội Bộ → Recruitment

## Mục tiêu
Đảm bảo classifier không phân loại nhầm email nội bộ/cá nhân thành recruitment.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/gmail/infrastructure/ai_classifier.py`
- `backend/src/modules/gmail/application/rules_classifier.py`

## Các bước thực hiện

1. **Email nội bộ về tuyển dụng**: HR gửi "Tuần này mình có 3 bạn đến phỏng vấn nhé"
   - Expected: KHÔNG phải `recruitment`, nên là `internal`

2. **Email forward nội bộ**: Forward email ứng tuyển từ HR cho đồng nghiệp
   - Expected: vẫn có thể `recruitment` nhưng source cần đánh dấu forwarded

3. **Email cá nhân**: "Chiều nay đi cafe không em?"
   - Expected: KHÔNG phải `recruitment`, nên là `uncategorized` hoặc `internal`

4. **Email newsletter**: "Top CV mẫu cho developer 2026" từ blog
   - Expected: KHÔNG phải `recruitment`, nên là `uncategorized` hoặc `vendor`

5. **Email system notification**: "Your Gmail storage is 90% full"
   - Expected: `notification`

## Kết quả mong đợi
- Internal email không vào Recruitment Inbox
- False positive rate < 5%

## Test files
- `backend/tests/modules/gmail/test_classify_integration.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
