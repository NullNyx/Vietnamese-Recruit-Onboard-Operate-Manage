# 03 — CV Parsing

Parse CV thành dữ liệu có cấu trúc qua AI pipeline.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-structured-parsing.md` | Parse CV đúng các field: skills, experience, education, summary | High |
| 02 | `02-no-cv-email.md` | Email không có CV — không parse | High |
| 03 | `03-corrupted-cv.md` | CV hỏng, sai format — xử lý graceful | Medium |

## Code liên quan

- `backend/src/modules/recruitment/application/intent_classifier.py` (CV processing)
- `backend/src/modules/recruitment/infrastructure/llm_adapter.py`
- `backend/tests/modules/recruitment/test_cv_processor.py`
- `backend/tests/modules/recruitment/test_cv_processor_integration.py`
