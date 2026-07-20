# 04 — Employee ID Injection: LLM Không Thể Thay Đổi

## Mục tiêu
Xác minh employee_id được tiêm từ session, LLM không thể override.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/assistant/application/employee_tool_registry.py`
- `backend/src/modules/assistant/application/employee_assistant_service.py`

## Các bước thực hiện

1. **LLM gửi employee_id khác trong args**:
   - Employee A (ID: aaa) đăng nhập, chat: "Xem hồ sơ của employee bbb"
   - LLM gọi get_my_profile với args `{"employee_id": "bbb"}`
   - Expected: `args.pop("employee_id", None)` → bỏ qua, luôn dùng `self._employee_id` (aaa)

2. **Tấn công qua tool argument**:
   - LLM cố gọi get_my_profile với `{"employee_id": "admin-user-id"}`
   - Expected: vẫn trả về profile của employee A

3. **Tấn công qua nhiều tool**:
   - LLM gọi list_my_payslips với `{"employee_id": "bbb"}`
   - Expected: args.pop → ignored, vẫn lấy payslips của A

4. **No write tool exposed**:
   - Prompt LLM: "Hãy gửi đơn nghỉ phép giúp tôi"
   - LLM gọi draft_leave_request → trả về Draft Action
   - Employee confirm trên UI → frontend gọi endpoint write
   - Expected: LLM không trực tiếp gọi write endpoint

5. **Tool không tồn tại**:
   - LLM hallucinate tên tool "update_salary"
   - Expected: `{"error": "Không thể xử lý yêu cầu"}` (generic error, no leak)

## Kết quả mong đợi
- `employee_id` bất biến từ session, strip mọi injection từ LLM
- Không có write tool trong registry
- Generic error message, không leak internal info

## Test files
- `backend/tests/modules/assistant/test_employee_tool_safety.py`
- `backend/tests/modules/assistant/test_employee_no_write.py`
- `backend/tests/modules/assistant/test_base_safety.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
