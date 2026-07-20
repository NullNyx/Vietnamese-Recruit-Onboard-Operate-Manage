# 08 — Rollout & Telemetry

Shadow/Canary/Full rollout, guardrails, telemetry accuracy, cost tracking.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-shadow-canary.md` | Shadow không duplicate, canary promote đúng | Medium |
| 02 | `02-operational-guardrails.md` | Guardrail chặn full rollout khi vi phạm | Medium |
| 03 | `03-telemetry-accuracy.md` | Telemetry chính xác sau retry, latest event | Medium |
| 04 | `04-cost-tracking.md` | Token usage → cost calculation chính xác | Medium |

## Code liên quan

- `backend/src/modules/gmail/application/classification_rollout.py`
- `backend/src/modules/gmail/application/classification_telemetry.py`
- `backend/src/modules/gmail/infrastructure/classification_rollout_repository.py`
- `backend/tests/modules/gmail/test_classification_rollout.py`
- `backend/tests/modules/gmail/test_classification_telemetry.py`
