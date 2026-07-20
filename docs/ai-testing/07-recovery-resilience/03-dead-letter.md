# 03 — Dead Letter: Permanent Failure Không Mất Dữ Liệu

## Mục tiêu
Xác minh email/CV permanent failure được giữ lại, không bị xóa.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/gmail/application/classification_service.py`
- `backend/src/modules/recruitment/domain/enums.py` (`permanently_failed`)

## Các bước thực hiện

1. **Email permanent failure**: 
   - Provider fail 3 lần → manual retry cũng fail
   - Expected: status = `permanently_failed`, giữ lại trong DB

2. **CV parsing permanent failure**:
   - CV corrupt, parse fail liên tục
   - Expected: status = `permanently_failed`, CV file vẫn trong MinIO

3. **Dead letter visible trong UI**:
   - Recruitment Inbox hiển thị item `permanently_failed`
   - Expected: HR thấy được, có thể xóa thủ công nếu không cần

4. **Disable capability không xóa pending**:
   - HR disable AI Automation capability
   - Expected: pending item không bị xóa, giữ nguyên trạng thái

5. **Cleanup policy**:
   - Dead letter tồn tại > 90 ngày
   - Expected: có cơ chế cleanup (nếu có), hoặc HR tự xóa

## Kết quả mong đợi
- Không mất dữ liệu
- Permanent failure item vẫn visible
- Không tự động xóa

## Test files
- `backend/tests/modules/gmail/test_classify_dead_letter.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
