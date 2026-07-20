# 01 — Tool Boundary: Chỉ Read + Draft

## Mục tiêu
Xác minh không tồn tại Write-Tool, LLM không thể ghi database trực tiếp.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/assistant/domain/tools.py` (`ToolKind`: chỉ `READ` và `DRAFT`)
- `backend/src/modules/assistant/application/tool_registry.py`
- `backend/src/modules/assistant/application/employee_tool_registry.py`

## Các bước thực hiện

1. **Kiểm tra tất cả tool definition**:
   - Duyệt TOOL_DEFINITIONS + EMPLOYEE_TOOL_DEFINITIONS
   - Expected: tất cả tool có kind ∈ {READ, DRAFT}, không có kind nào khác

2. **Registry từ chối tool không tồn tại**:
   - Gọi tool "update_candidate_status"
   - Expected: `{"error": "Unknown tool: ..."}` hoặc generic error

3. **Draft-Tool không gọi service write**:
   - Gọi draft_interview_invitation → kiểm tra DB
   - Expected: không có email nào được gửi, không có record mới

4. **Draft-Tool chỉ trả về proposal**:
   - Expected: response chứa `draft_action` với confirm_endpoint, confirm_body
   - Frontend phải tự gọi confirm_endpoint

5. **Không có endpoint write trong tool registry**:
   - Search code: không có `ToolKind.WRITE`
   - Expected: `ToolKind` enum chỉ có READ, DRAFT

## Kết quả mong đợi
- Structural safety: không thể thêm Write tool nếu không sửa enum
- Draft action không tự động execute

## Test files
- `backend/tests/modules/assistant/test_domain_tools.py`
- `backend/tests/modules/assistant/test_base_safety.py`
- `backend/tests/modules/assistant/test_hr_tool_safety.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
