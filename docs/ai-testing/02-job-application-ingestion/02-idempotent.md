# 02 — Idempotent: Không Tạo Duplicate JobApplication

## Mục tiêu
Xác minh classify_batch không tạo duplicate JobApplication khi chạy lại trên cùng email.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/recruitment/application/job_application_service.py`
- `backend/src/modules/recruitment/infrastructure/repositories.py` (JobApplicationRepository)

## Các bước thực hiện

1. **Classify lần đầu**: email mới → tạo JobApplication (1 record)
   - Expected: 1 JobApplication trong DB

2. **Classify lại cùng email**: gọi classify_batch lần nữa
   - Expected: vẫn chỉ 1 JobApplication (không duplicate)

3. **Classify lại sau restart**: restart backend → classify lại
   - Expected: vẫn 1 JobApplication (idempotent dựa trên `gmail_message_id`)

4. **Classify sau khi JobApplication bị xóa**: xóa JobApplication → classify lại
   - Expected: JobApplication mới được tạo (vì đã xóa)

5. **Nhiều email khác nhau cùng sender**: cùng sender gửi 2 email khác nhau
   - Expected: 2 JobApplication riêng biệt (khác `gmail_message_id`)

## Kết quả mong đợi
- Key idempotent = `gmail_message_id`
- `get_by_gmail_message_id` trả về record hiện có

## Test files
- `backend/tests/modules/gmail/test_job_application_ingestion.py`
- `backend/tests/modules/gmail/test_job_application_persistence_integration.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
