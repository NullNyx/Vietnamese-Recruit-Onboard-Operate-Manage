# 04 — Không Bỏ Sót Job Application (Recall ≥ 98%)

## Mục tiêu
Đảm bảo classifier không bỏ sót email ứng tuyển, đặc biệt các edge case khó.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/gmail/application/classification_service.py`
- `backend/src/modules/gmail/infrastructure/ai_classifier.py`
- `backend/src/modules/gmail/evaluation/`

## Điều kiện tiên quyết
- AI Evaluation Set có sẵn các mẫu email khó
- Script evaluate_baseline.py hoạt động

## Các bước thực hiện

### Nhóm email dễ bỏ sót

1. **Email không CV, body ngắn**: "Em tên A, muốn xin việc. SĐT 09xx"
   - Expected: classification = `recruitment`, intent = `job_application`

2. **Email tiếng Việt không dấu**: "e ten B, e muon ung tuyen vi tri designer"
   - Expected: vẫn phân loại đúng `recruitment`

3. **Email từ Gmail cá nhân**: "@gmail.com", subject "Xin việc"
   - Expected: không bị bỏ qua vì domain không phải job board

4. **Email referral không rõ ràng**: "Thằng em cùng lớp em mới ra trường, đang tìm việc"
   - Expected: nhận diện intent `job_application`, vào Recruitment Inbox

5. **Email với CV dạng link**: "CV của em: https://drive.google.com/..."
   - Expected: vẫn phân loại `recruitment`, không cần attachment

6. **Email tiếng Anh + tiếng Việt lẫn lộn**: subject "Application for Senior Dev", body tiếng Việt
   - Expected: phân loại đúng

### Đo lường

7. **Chạy evaluation set**: `python backend/scripts/evaluate_baseline.py`
   - Expected: recall ≥ 98% tổng thể, recall ≥ 95% cho nhóm khó

## Kết quả mong đợi
- Recall tổng thể ≥ 98%
- Recall nhóm "không CV" ≥ 95%
- False negative rate < 2%

## Test files
- `backend/scripts/evaluate_baseline.py`
- `backend/tests/modules/gmail/test_evaluation.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)

## Ghi chú
Đây là hard guardrail trong ADR-0005. Nếu recall < 98% thì không được promote classifier mới lên production.
