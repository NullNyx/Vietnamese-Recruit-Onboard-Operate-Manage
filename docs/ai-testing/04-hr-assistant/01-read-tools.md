# 01 — 8 Read-Tools Trả Về Dữ Liệu Chính Xác

## Mục tiêu
Xác minh tất cả Read-Tools trả về dữ liệu live, chính xác từ database.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/assistant/domain/tools.py` (TOOL_DEFINITIONS)
- `backend/src/modules/assistant/application/tool_registry.py` (ToolRegistry)

## Các bước thực hiện

### Test từng Read-Tool

1. **count_candidates_by_status**: 
   - Gọi không filter → trả về count cho tất cả status
   - Gọi với status="new" → chỉ trả về count của new
   - Gọi với status="invalid" → trả về error với valid status list

2. **search_candidates**:
   - Tìm theo tên có thật → trả về danh sách candidate
   - Tìm với query rỗng → trả về error
   - Tìm tên không tồn tại → trả về empty list

3. **get_candidate_parsed_cv**:
   - Gọi với candidate_id hợp lệ → trả về parsed_cv_json, skills, experience
   - Gọi với UUID không tồn tại → trả về error
   - Gọi với UUID sai format → trả về error

4. **list_interviews_for_candidate**:
   - Candidate có 3 interviews → trả về 3 record
   - Candidate không có interview → trả về empty list

5. **list_job_openings**:
   - Gọi mặc định → trả về status="open"
   - Gọi với status="draft" → trả về draft openings
   - Gọi với status không hợp lệ → error

6. **get_department_info**:
   - Gọi không department_id → trả về tất cả departments
   - Gọi với department_id → trả về 1 department + positions + managers

7. **list_in_progress_onboarding**:
   - Có onboarding đang chạy → trả về danh sách
   - Không có → trả về empty list

8. **get_onboarding_task_details**:
   - Gọi với process_id hợp lệ → trả về tasks + status

## Kết quả mong đợi
- Dữ liệu trả về khớp với database
- Error message rõ ràng, không leak internal info
- Response format nhất quán (JSON)

## Test files
- `backend/tests/modules/assistant/test_tool_registry.py`
- `backend/tests/modules/assistant/test_tool_boundary.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
