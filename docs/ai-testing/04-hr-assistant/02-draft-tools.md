# 02 — 2 Draft-Tools Tạo Draft Action Đúng Format

## Mục tiêu
Xác minh Draft-Tools trả về Draft Action có cấu trúc đúng, HR confirm được.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/assistant/domain/tools.py` (DraftAction)
- `backend/src/modules/assistant/application/tool_registry.py`

## Các bước thực hiện

### draft_interview_invitation

1. **Draft với đủ tham số**: candidate_id, interview_date, interview_time, location
   - Expected: DraftAction với:
     - `action_type` = "send_email"
     - `preview` = mô tả tiếng Việt
     - `provenance` = có tool, scope, assistant_type, redacted, candidate_id
     - `confirm_endpoint` = `/api/recruitment/candidates/{id}/send-email`
     - `confirm_method` = "POST"
     - `confirm_body` = `{subject, body_html}`

2. **Draft với candidate_id không tồn tại**:
   - Expected: error message "Không tìm thấy ứng viên"

3. **Draft thiếu tham số**: thiếu interview_time
   - Expected: error "Missing required parameters"

4. **HTML escaping**: candidate tên `<script>alert('xss')</script>`
   - Expected: tên bị escape trong body_html

### draft_congratulations_email

5. **Draft với đủ tham số**: candidate_id, position, start_date
   - Expected: tương tự như trên, preview "Gửi thư trúng tuyển vị trí {position}"

## Kết quả mong đợi
- Draft Action không gọi write endpoint
- Provenance có đầy đủ metadata
- Frontend có thể dùng confirm_endpoint để gọi thật

## Test files
- `backend/tests/modules/assistant/test_tool_registry.py`
- `backend/tests/modules/assistant/test_tool_boundary.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
