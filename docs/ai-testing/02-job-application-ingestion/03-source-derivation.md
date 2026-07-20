# 03 — Source Derivation Chính Xác

## Mục tiêu
Xác minh ApplicationSource được derive đúng từ matched_signals của ClassificationResult.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/recruitment/application/job_application_service.py`
- `backend/src/modules/recruitment/domain/enums.py` (ApplicationSource)

## Các bước thực hiện

1. **Direct**: matched_signals chứa `subject:ứng tuyển` hoặc `sender_role:candidate`
   - Expected: `source` = `direct`, `applicant_name`/`applicant_email` = sender

2. **Employee Referral**: matched_signals chứa `referral`
   - Expected: `source` = `employee_referral`, `applicant_name`/`applicant_email` = null

3. **Agency/Headhunter**: matched_signals chứa `agency` hoặc `headhunter`
   - Expected: `source` = `agency`, `applicant_name`/`applicant_email` = null

4. **Job Board**: sender domain là vietnamworks.com, topcv.vn
   - Expected: `source` = `direct` (ứng viên tự ứng tuyển qua job board)

5. **Không có signal**: không matched_signal đặc biệt → default
   - Expected: `source` = `direct` (fallback hợp lý)

## Kết quả mong đợi
- 3 source được phân biệt rõ: direct, employee_referral, agency
- Applicant identity policy: direct → copy từ sender; referral/agency → null

## Test files
- `backend/tests/modules/gmail/test_job_application_ingestion.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
