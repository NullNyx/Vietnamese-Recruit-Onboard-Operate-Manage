# Task
Thêm 2 Read-Tool mới vào HR Assistant: `list_job_openings` (Issue #231) và `get_department_info` (Issue #232).

# What I changed
- **`tools.py`**: Thêm `ToolDefinition` cho `list_job_openings` (READ, param: status optional, default open) và `get_department_info` (READ, param: department_id optional UUID)
- **`tool_registry.py`**: 
  - Thêm `session` và `department_service` params vào `__init__` (optional, backward compatible)
  - Thêm TYPE_CHECKING imports: `AsyncSession`, `DepartmentService`
  - Thêm `_VALID_JOB_OPENING_STATUSES` constant
  - Thêm handler `_list_job_openings` — validate status, query JobOpeningRepository, resolve position → department, batch-count accepted candidates
  - Thêm handler `_get_department_info` — validate UUID (optional), query Department/Position/Employee entities, return structured department info
  - Thêm cả 2 tools vào handlers dict
- **`container.py`**: Cập nhật `get_tool_registry` dependency injection — inject thêm `session` (AsyncSession) và `department_service` (DepartmentService)
- **`test_tool_registry.py`**: Thêm 10 tests mới — 6 cho `list_job_openings` (invalid status, default open, no session, not found, valid call with position/department, filter) + 4 cho `get_department_info` (invalid UUID, not found, list all, no session)

# The real problem
HR Assistant không có khả năng query về job openings và department structure. Khi HR hỏi "có bao nhiêu job opening đang open?" hoặc "phòng Engineering có bao nhiêu người?", LLM không trả lời được.

# Why this solution
- **Pattern nhất quán**: Giống hệt các Read-Tool hiện có — validate params → call service/repo → format JSON → return
- **Dùng session để query cross-module**: Thay vì inject nhiều service riêng, dùng `AsyncSession` để query trực tiếp các entity từ employee module (Department, Position, Employee)
- **JobOpeningRepository cho recruitment queries**: Dùng sẵn `list_job_openings()` và `count_accepted_by_job_opening()` từ recruitment module
- **Backward compatible**: `session` và `department_service` là optional params, không break code cũ
- **Batch query optimization**: Position và Department names được resolve theo batch (1 query per entity type), không N+1

# Production shape

**list_job_openings:**
```json
{
  "job_openings": [
    {
      "id": "uuid",
      "title": "Senior Developer",
      "department": "Engineering",
      "position": "Senior Developer",
      "headcount_target": 3,
      "headcount_filled": 1,
      "status": "open"
    }
  ],
  "total": 1,
  "status": "open"
}
```

**get_department_info:**
```json
{
  "departments": [
    {
      "id": "uuid",
      "name": "Engineering",
      "description": "Engineering department",
      "positions": [
        {"position_title": "Senior Developer", "employee_count": 5}
      ],
      "managers": [
        {"id": "uuid", "full_name": "Nguyen Van A", "email": "a@example.com", "position_id": "uuid"}
      ],
      "employee_count": 10
    }
  ],
  "total": 1
}
```

# Other possible approaches
1. **Inject JobOpeningService + DepartmentService thay vì session**: Cần user_id cho JobOpeningService (write audit), không phù hợp read-only
2. **Thêm method mới vào service layer**: Phức tạp hơn, cần sửa nhiều file, vi phạm single responsibility của service
3. **Dùng repository pattern cho mọi entity**: Over-engineer cho 2 Read-Tool, session+SQLModel query đủ

# Why I did not choose those alternatives
- JobOpeningService cần user_id — không có context user trong tool registry; thêm fake user_id là anti-pattern
- Thêm service method = thêm layer không cần thiết cho read-only query aggregate
- Repository cho Position/Department: đã có sẵn session, SQLModel select đơn giản hơn

# Key concepts to learn
- Cross-module query trong monolith: assistant module query thẳng employee entities qua session (ADR-0004 one-way dependency vẫn giữ — assistant không expose API, chỉ gọi query)
- Batch resolve relationships: Position → Department batch query giảm N+1
- Optional session pattern: ToolRegistry vẫn hoạt động nếu không có session — tool trả về error message thay vì crash
- `headcount_filled` = accepted candidates count, không phải headcount_target - headcount_filled (có thể overfill)
