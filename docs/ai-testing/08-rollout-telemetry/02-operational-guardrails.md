# 02 — Operational Guardrails Chặn Rollout

## Mục tiêu
Xác minh các operational guardrail (latency, error rate, retry failure) chặn rollout khi vi phạm.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/gmail/application/classification_rollout.py`

## Các bước thực hiện

1. **p95 latency > threshold**:
   - Candidate classifier có p95 = 2.5s (threshold = 2.0s)
   - Expected: không promote được, failure_code = "p95_latency_exceeded"

2. **Provider error rate > threshold**:
   - Candidate classifier có provider error = 10% (threshold = 5%)
   - Expected: failure_code = "provider_error_rate_exceeded"

3. **Retry failure rate > threshold**:
   - Candidate classifier có retry failure = 8% (threshold = 5%)
   - Expected: failure_code = "retry_failure_rate_exceeded"

4. **Tất cả guardrail pass**:
   - Recall ≥ 98%, p95 < 2s, error < 5%, retry failure < 5%
   - Expected: có thể promote lên full

5. **Active rollout vi phạm guardrail**:
   - Đang full rollout, bỗng provider error tăng
   - Expected: auto-rollback về stable

6. **Không cho HR tự set threshold**:
   - Expected: threshold được giữ trong module rollout, không expose cho UI tùy chỉnh

## Kết quả mong đợi
- Hard guardrail (recall) + operational guardrail (latency, error, retry)
- Failure codes có cấu trúc
- Auto-rollback khi active vi phạm

## Test files
- `backend/tests/modules/gmail/test_classification_rollout.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
