# 04 — Callback Failure Không Ảnh Hưởng Classification

## Mục tiêu
Xác minh khi JobApplication creation callback thất bại, classification vẫn preserved.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/gmail/application/classification_service.py`
- `backend/src/modules/recruitment/application/job_application_service.py`

## Các bước thực hiện

1. **JobApplicationService lỗi DB**: simulate DB connection error khi tạo JobApplication
   - Expected: email vẫn được đánh dấu `classified`, category vẫn được lưu

2. **JobApplicationService raise exception**: simulate bug trong service
   - Expected: exception được catch trong try/except, classification không fail

3. **Provider lỗi trước classification**: LLM provider unavailable
   - Expected: email giữ trạng thái an toàn, có thể retry sau

4. **Transaction rollback test**: JobApplication fail → classification có rollback không?
   - Expected: classification KHÔNG rollback (tách biệt)

## Kết quả mong đợi
- Callback failure → log warning, không crash
- Email classification preserved
- JobApplication có thể được tạo lại sau khi fix lỗi

## Test files
- `backend/tests/modules/gmail/test_job_application_ingestion.py`
- `backend/tests/modules/gmail/test_classify_preservation.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
