# 07 — Recovery & Resilience

Provider failure, retry, manual recovery, dead letter.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-provider-failure-retry.md` | Retry với backoff, không silent fail | Critical |
| 02 | `02-manual-recovery.md` | HR retry thủ công/phân loại thủ công | High |
| 03 | `03-dead-letter.md` | Permanent failure → dead letter, không mất | High |
| 04 | `04-provider-fallback.md` | Fallback graceful, không gộp thành other | Medium |

## Code liên quan

- `backend/src/modules/gmail/application/classification_service.py`
- `backend/src/modules/gmail/application/provider_fallback.py`
- `backend/src/modules/gmail/infrastructure/ai_classifier.py`
- `backend/tests/modules/gmail/test_ai_automation_recovery.py`
- `backend/tests/modules/gmail/test_classify_dead_letter.py`
- `backend/tests/modules/gmail/test_classify_timeout.py`
