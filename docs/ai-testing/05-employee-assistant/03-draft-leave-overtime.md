# 03 — Draft-Tools: Đơn Nghỉ Phép & Tăng Ca

## Mục tiêu
Xác minh Draft-Tools tạo đơn nghỉ phép và tăng ca đúng format, có validation.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/assistant/application/employee_tool_registry.py`
- `backend/src/modules/assistant/domain/employee_tools.py`

## Các bước thực hiện

### draft_leave_request

1. **Draft hợp lệ**: leave_type="annual", start_date="2026-08-01", end_date="2026-08-03", reason="Nghỉ hè"
   - Expected: DraftAction với:
     - `action_type` = "submit_leave_request"
     - `provenance.assistant_type` = "employee_assistant"
     - `provenance.scope` = "employee_self_service"
     - `confirm_endpoint` = "/api/employee-requests/me/leave"
     - `confirm_method` = "POST"

2. **Validation: end_date < start_date**: "2026-08-03" → "2026-08-01"
   - Expected: error "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu"

3. **Validation: leave_type không hợp lệ**: "vacation"
   - Expected: error "Loại nghỉ không hợp lệ: 'vacation'"

4. **Validation: date format sai**: "01/08/2026"
   - Expected: error "Ngày không hợp lệ. Định dạng: YYYY-MM-DD"

5. **Thiếu tham số**: thiếu reason
   - Expected: error "Thiếu thông tin"

### draft_overtime_request

6. **Draft hợp lệ**: work_date, start_time, end_time, reason, project_or_task
   - Expected: DraftAction với confirm_endpoint "/api/employee-requests/me/overtime"

7. **Validation: end_time ≤ start_time**: "18:00" → "17:00"
   - Expected: error "Giờ kết thúc phải sau giờ bắt đầu"

## Kết quả mong đợi
- Validation chạy trước khi tạo Draft Action
- Provenance có assistant_type = "employee_assistant"
- Confirm endpoint trỏ đúng API

## Test files
- `backend/tests/modules/assistant/test_employee_no_write.py`
- `backend/tests/modules/assistant/test_employee_tool_boundary.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
