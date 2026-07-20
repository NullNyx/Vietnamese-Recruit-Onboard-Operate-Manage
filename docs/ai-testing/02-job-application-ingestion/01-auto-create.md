# 01 — Tự Động Tạo JobApplication Khi Confident

## Mục tiêu
Xác minh hệ thống tự động tạo JobApplication khi email được phân loại `recruitment` với confidence cao.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/recruitment/application/job_application_service.py` (`create_from_classification`)
- `backend/src/modules/gmail/application/classification_service.py`

## Điều kiện tiên quyết
- Gmail đã sync email
- Classification đã chạy
- AI Automation capability được bật

## Các bước thực hiện

1. **Email confident recruitment từ direct applicant**: sender "@gmail.com", subject "Ứng tuyển Backend", confidence ≥ 0.9
   - Expected: JobApplication được tạo với:
     - `status` = `new`
     - `source` = `direct`
     - `applicant_name` = sender name
     - `applicant_email` = sender email
     - `gmail_message_id` = email message ID từ Gmail

2. **Email confident recruitment từ agency**: sender "@headhunt.vn", confidence ≥ 0.9
   - Expected: JobApplication với `source` = `agency`, `applicant_name`/`applicant_email` = null

3. **Email KHÔNG phải recruitment**: confidence cao nhưng category = `internal`
   - Expected: KHÔNG tạo JobApplication

4. **Email recruitment confidence thấp**: confidence < threshold
   - Expected: KHÔNG tạo JobApplication, email vào needs_review

## Kết quả mong đợi
- JobApplication chỉ được tạo khi category = recruitment + confidence đủ cao
- Source được derive đúng
- Applicant identity phù hợp với source

## Test files
- `backend/tests/modules/gmail/test_job_application_ingestion.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
