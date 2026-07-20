# 01 — 7 Read-Tools Trả Về Đúng Dữ Liệu Employee

## Mục tiêu
Xác minh tất cả Employee Read-Tools trả về dữ liệu chính xác, chỉ của employee hiện tại.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/assistant/domain/employee_tools.py` (EMPLOYEE_TOOL_DEFINITIONS)
- `backend/src/modules/assistant/application/employee_tool_registry.py`

## Các bước thực hiện

### Test từng tool với employee đã authenticate

1. **get_my_profile**: employee A đăng nhập
   - Expected: trả về full_name, email, phone, department, position, start_date của A

2. **list_my_documents**:
   - Expected: chỉ trả về documents của A, không của B

3. **get_today_attendance**:
   - Hôm nay đã check-in → trả về check_in_at, status="present"
   - Hôm nay chưa check-in → trả về status="not_checked_in"

4. **list_my_attendance_records**: gọi với month=7, year=2026
   - Expected: chỉ records của A trong tháng 7

5. **list_my_employee_requests**:
   - Gọi không filter → trả về cả leave và overtime
   - Gọi request_type="leave" → chỉ leave requests

6. **get_my_leave_balance**:
   - Expected: entitlement, used, pending, remaining, as_of

7. **list_my_payslips**:
   - Expected: chỉ payslips của A, không của B

## Kết quả mong đợi
- Dữ liệu luôn thuộc về employee đã authenticate
- Không leak dữ liệu employee khác
- `args.pop("employee_id", None)` luôn được gọi để strip

## Test files
- `backend/tests/modules/assistant/test_employee_tool_boundary.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
