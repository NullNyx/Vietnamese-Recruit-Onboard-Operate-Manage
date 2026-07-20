# 02 — Job Application Ingestion

Tự động tạo JobApplication từ email đã phân loại + idempotent + source derivation.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-auto-create.md` | Tự động tạo JobApplication khi confident recruitment | Critical |
| 02 | `02-idempotent.md` | Không tạo duplicate JobApplication | Critical |
| 03 | `03-source-derivation.md` | Derive đúng ApplicationSource | High |
| 04 | `04-callback-failure.md` | Callback failure không ảnh hưởng classification | High |

## Code liên quan

- `backend/src/modules/recruitment/application/job_application_service.py`
- `backend/src/modules/recruitment/domain/entities.py` (JobApplication)
- `backend/src/modules/recruitment/domain/enums.py` (ApplicationSource, JobApplicationStatus)
- `backend/src/modules/gmail/application/classification_service.py`
- `backend/tests/modules/gmail/test_job_application_ingestion.py`
