# 01 — Shadow/Canary Rollout Không Gây Duplicate

## Mục tiêu
Xác minh shadow classifier không tạo duplicate workflow, canary promote có điều kiện.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/gmail/application/classification_rollout.py`
- `backend/src/modules/gmail/infrastructure/classification_rollout_repository.py`

## Các bước thực hiện

1. **Shadow mode**: 
   - Enable shadow cho classifier version mới
   - Classifier mới chạy song song với stable
   - Expected: 
     - Stable vẫn là active classifier
     - Shadow ghi kết quả evaluation, KHÔNG tạo JobApplication
     - Không duplicate workflow

2. **Shadow recall đạt yêu cầu**:
   - Shadow classifier có recall ≥ 98%
   - Expected: có thể promote lên canary

3. **Canary mode**:
   - Promote lên canary (một phần traffic)
   - Expected: candidate classifier xử lý subset email, ghi comparison data

4. **Canary → Full bị chặn vì guardrail**:
   - Candidate có recall tốt nhưng p95 latency > 2s
   - Expected: không promote được, trả failure codes

5. **Rollback về stable**:
   - Full rollout gặp vấn đề → rollback
   - Expected: stable version được giữ lại, có thể switch ngay

## Kết quả mong đợi
- Shadow không ảnh hưởng production
- Canary/Full có guardrail
- Stable retained để rollback

## Test files
- `backend/tests/modules/gmail/test_classification_rollout.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
