# 05 — Provenance Và Audit Decision

## Mục tiêu
Xác minh provenance được ghi nhận trong Draft Action và audit decision hoạt động.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/assistant/domain/tools.py` (DraftAction.provenance)
- `backend/src/modules/assistant/api/router.py` (draft-decision endpoint)

## Các bước thực hiện

1. **Provenance trong Draft Action**:
   - Gọi draft_interview_invitation
   - Expected: `provenance` = `{tool, scope, assistant_type, redacted: true, candidate_id, source_fields}`

2. **Confirm Draft Action**:
   - HR click confirm trên UI
   - Expected: frontend gọi `confirm_endpoint` với `confirm_body`
   - Backend ghi audit event: action_type, scope, tool, version, candidate_id (redacted)

3. **Reject Draft Action**:
   - HR click reject
   - Expected: gọi draft-decision endpoint với status="rejected"
   - Audit ghi nhận reject, không gửi email

4. **Không có raw conversation trong audit**:
   - Expected: audit table không chứa body email hoặc raw prompt

5. **Provenance không bị client giả mạo**:
   - Gửi trực tiếp confirm body với provenance fake
   - Expected: backend verify provenance, từ chối nếu không hợp lệ

## Kết quả mong đợi
- Provenance đầy đủ metadata
- Audit không chứa PII hoặc raw conversation
- Confirm/reject được ghi nhận

## Test files
- `backend/tests/modules/assistant/test_tool_boundary.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
