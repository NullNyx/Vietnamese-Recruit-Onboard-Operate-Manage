# 01 — Email Classification

Phân loại email đầu vào: rule-based classifier + AI classifier (LLM) + intent classifier.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-rules-classifier.md` | Rule-based phân loại đúng 15 category | Critical |
| 02 | `02-ai-classifier.md` | AI classifier xử lý email ambiguous | Critical |
| 03 | `03-intent-classifier.md` | Intent classifier phân biệt job_application/partner/event/internal/other | Critical |
| 04 | `04-missing-job-application.md` | Không bỏ sót job application (recall ≥ 98%) | Critical |
| 05 | `05-false-positive.md` | Không phân loại nhầm email nội bộ thành recruitment | Critical |
| 06 | `06-multiple-cv-in-email.md` | Agency gửi nhiều CV trong 1 email | High |
| 07 | `07-vietnamese-edge-cases.md` | Email tiếng Việt, không dấu, teencode | High |

## Code liên quan

- `backend/src/modules/gmail/infrastructure/ai_classifier.py`
- `backend/src/modules/gmail/application/rules_classifier.py`
- `backend/src/modules/gmail/application/classification_service.py`
- `backend/src/modules/recruitment/application/intent_classifier.py`
- `backend/tests/modules/gmail/test_classify_*.py`
- `backend/tests/modules/recruitment/test_intent_classifier.py`
