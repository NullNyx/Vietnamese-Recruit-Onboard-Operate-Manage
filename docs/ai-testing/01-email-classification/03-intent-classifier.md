# 03 — Intent Classifier Phân Biệt Intent Email

## Mục tiêu
Xác minh intent classifier phân biệt đúng 5 intent: job_application, partner, event, internal, other.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/recruitment/application/intent_classifier.py`
- `backend/src/modules/recruitment/domain/enums.py` (EmailIntent)
- `backend/src/modules/recruitment/infrastructure/pii_redactor.py`

## Điều kiện tiên quyết
- LLM provider hoạt động
- Email đã được sync từ Gmail

## Các bước thực hiện

1. **Email ứng tuyển có CV**: subject "Ứng tuyển Backend", attachment CV.pdf
   - Expected: intent = `job_application`

2. **Email ứng tuyển KHÔNG CV**: body "Em muốn ứng tuyển vị trí Frontend, em chưa có CV"
   - Expected: intent = `job_application` (intent là ý định, không phụ thuộc CV)

3. **Email từ headhunter**: "Bên em có 3 ứng viên Java senior"
   - Expected: intent = `partner`, source = `agency`

4. **Email từ nhân viên giới thiệu**: "Bạn em tên C học RMIT, anh xem giúp"
   - Expected: intent = `job_application`, source = `employee_referral`

5. **Email event**: "Mời tham dự ngày hội việc làm UIT 2026"
   - Expected: intent = `event`

6. **Email internal**: "Báo cáo KPI quý 2"
   - Expected: intent = `internal`

7. **PII redaction**: email chứa số điện thoại, CMND trong body
   - Expected: PII bị redact trước khi gửi LLM

## Kết quả mong đợi
- Intent phân biệt đúng, không nhầm internal → job_application
- Source được derive từ matched_signals
- PII không bị gửi lên LLM provider

## Test files
- `backend/tests/modules/recruitment/test_intent_classifier.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
