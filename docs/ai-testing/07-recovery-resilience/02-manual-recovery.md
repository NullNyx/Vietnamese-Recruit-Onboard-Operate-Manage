# 02 — Manual Recovery: HR Retry / Phân Loại Thủ Công

## Mục tiêu
Xác minh HR có thể retry thủ công hoặc phân loại thủ công khi provider unavailable kéo dài.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/gmail/application/classification_service.py`
- Gmail API endpoints
- Recruitment Inbox UI

## Các bước thực hiện

1. **HR retry email pending**:
   - Email ở trạng thái `pending_classification` với `ai_unavailable`
   - HR click "Retry" trên UI
   - Expected: gọi classify lại, nếu provider up thì phân loại thành công

2. **HR phân loại thủ công**:
   - HR mở email trong Recruitment Inbox
   - Chọn category thủ công: recruitment, interview, etc.
   - Expected: category được lưu, `source = "manual"`, email marked classified

3. **HR retry CV parsing**:
   - CV parse failed → HR click "Retry Parse"
   - Expected: gọi lại CV processor

4. **Manual classification audit**:
   - Expected: audit ghi nhận ai phân loại, thời gian, category cũ vs mới

5. **Batch retry**:
   - HR chọn nhiều email pending → "Retry All"
   - Expected: từng email được retry tuần tự

## Kết quả mong đợi
- HR có thể retry hoặc phân loại thủ công
- Audit ghi nhận manual action
- Không yêu cầu restart backend

## Test files
- `backend/tests/modules/gmail/test_classify_dead_letter.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
