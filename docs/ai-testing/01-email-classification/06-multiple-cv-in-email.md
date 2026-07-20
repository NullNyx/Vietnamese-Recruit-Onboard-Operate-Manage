# 06 — Agency Gửi Nhiều CV Trong 1 Email

## Mục tiêu
Xác minh hệ thống tạo đúng số lượng JobApplication khi 1 email chứa nhiều CV.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/recruitment/application/job_application_service.py`
- `backend/src/modules/gmail/application/classification_service.py`

## Các bước thực hiện

1. **Agency gửi 3 CV**: 1 email, 3 file PDF đính kèm, body "Bên em gửi 3 ứng viên Java: A, B, C"
   - Expected: 3 JobApplication được tạo (1 cho mỗi CV), cùng `gmail_message_id`
   - Source = `agency`
   - `applicant_name`, `applicant_email` = null (vì sender là agency, không phải applicant)

2. **Referral gửi 2 CV**: "2 đứa em em gửi CV, xếp xem giúp"
   - Expected: 2 JobApplication, source = `employee_referral`

3. **Email có cả CV và link**: 1 file PDF + 2 link Google Drive
   - Expected: 3 JobApplication được tạo (1 từ attachment + 2 từ link)

4. **Idempotent khi classify lại**: classify_batch gọi lại trên cùng email
   - Expected: không tạo duplicate JobApplication

## Kết quả mong đợi
- Mỗi CV riêng biệt → 1 JobApplication riêng
- Tất cả cùng tham chiếu `gmail_message_id` gốc
- Không có CV nào bị bỏ sót

## Test files
- `backend/tests/modules/gmail/test_job_application_ingestion.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
