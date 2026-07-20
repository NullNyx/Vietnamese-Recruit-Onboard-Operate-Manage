# 01 — Provider Failure → Retry Với Backoff

## Mục tiêu
Xác minh khi LLM provider unavailable, hệ thống retry có giới hạn và không mất dữ liệu.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/gmail/infrastructure/ai_classifier.py` (`_BACKOFF_DELAYS = [1, 2, 4]`)
- `backend/src/modules/gmail/application/classification_service.py`

## Các bước thực hiện

1. **Provider timeout lần 1**: giả lập timeout 15s
   - Expected: retry sau 1s, `retry_count=1`

2. **Provider timeout lần 2**:
   - Expected: retry sau 2s, `retry_count=2`

3. **Provider timeout lần 3**:
   - Expected: retry sau 4s, `retry_count=3`

4. **Provider fail cả 3 lần**:
   - Expected: 
     - `ai_unavailable` = true
     - `next_retry_at` = now + 60s
     - Email giữ trạng thái `pending_classification`
     - KHÔNG chuyển thành `other` (không silent fail)

5. **Provider hồi phục sau fail**:
   - Retry lần 4 sau 60s
   - Expected: category được ghi, retry metadata reset

6. **Song song nhiều email fail**:
   - 10 email cùng fail provider
   - Expected: tất cả đều có `next_retry_at`, không bị dropout

## Kết quả mong đợi
- Backoff: 1s → 2s → 4s → manual (60s)
- Không silent fail
- Email không bị mất

## Test files
- `backend/tests/modules/gmail/test_ai_automation_recovery.py`
- `backend/tests/modules/gmail/test_classify_timeout.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
