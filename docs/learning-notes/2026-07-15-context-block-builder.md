# Task
Xây dựng ContextBlock Builder — infrastructure dynamic context injection cho AI Assistant (HR + Employee).

# What I changed
- **Thêm** `backend/src/modules/assistant/application/context_builder.py`: class `ContextBuilder` với `build_hr_context()` (org name, pipeline summary, open job openings, onboarding count) và `build_employee_context(employee_id)` (profile, leave balance, pending requests, payslips)
- **Sửa** `AssistantService`: `__init__` thêm optional `context_builder`, `_build_messages` → async, inject HR context block làm system message thứ hai sau static core prompt
- **Sửa** `EmployeeAssistantService`: tương tự, inject employee context block
- **Sửa** `container.py`: thêm `get_context_builder` FastAPI Depends provider, wire vào `get_assistant_service`
- **Sửa** `employee_router.py`: tạo ContextBuilder với employee deps, truyền vào EmployeeAssistantService
- **Sửa** 3 tests trong `test_tool_loop_fallback.py`: cập nhật từ sync → async vì `_build_messages` giờ là async

# The real problem
AI Assistant (cả HR và Employee) chỉ có system prompt tĩnh 12 dòng, không biết gì về dữ liệu thực tế của Organization. Khi HR hỏi "có bao nhiêu CV đang chờ review?", LLM không có context để trả lời nếu không gọi tool trước. Context block cung cấp thông tin nền để LLM hiểu bối cảnh trước khi quyết định gọi tool gì.

# Why this solution
- **Tách instruction khỏi data**: Core prompt (rules, constraints) là static string, context block (dữ liệu thực tế) là system message thứ hai. Dễ debug, dễ thay đổi từng phần độc lập.
- **Fail-safe**: Nếu build context lỗi (DB down, service lỗi), chat vẫn hoạt động bình thường - chỉ không có context bổ sung.
- **Backward compatible**: `context_builder=None` mặc định, code cũ và tests không bị ảnh hưởng.
- **Không cache**: Mỗi request build context fresh. Cache sẽ làm ticket riêng nếu cần tối ưu latency.

# Production shape
Mỗi lần HR/Employee chat:
1. Static system prompt (rules: no-write, tool usage)
2. **Context block** (system message #2): dữ liệu thực tế từ DB
3. User message + history

Ví dụ context block HR Assistant:
```
---
Tổ chức: Công ty TNHH ABC
Pipeline tuyển dụng (tổng 42 ứng viên):
  - mới: 15
  - đang xem xét: 8
  - đã lên lịch phỏng vấn: 5
  - đã trúng tuyển: 3
  - đã từ chối: 10
  - đã lưu trữ: 1
Vị trí đang tuyển (2):
  - Senior Backend Developer
  - UX Designer
Onboarding đang diễn ra: 3 nhân viên.
---
```

# Other possible approaches
1. **Template injection**: Prompt có placeholder `{org_name}`, fill lúc build → phức tạp hơn, khó debug, khó thêm field mới
2. **Gửi context qua user message**: Append context vào user message đầu tiên → LLM có thể ignore, vì nó nằm trong conversation history chứ không phải instruction
3. **Tool-based context**: LLM tự gọi tool để lấy context → tốn thêm 1-2 tool calls mỗi lần chat, latency cao hơn

# Why I did not choose those alternatives
- Template injection: phải sửa prompt template mỗi khi thêm field context mới, không tách biệt được instruction vs data
- User message injection: LLM không có obligation phải đọc kỹ user message như system message; dễ bị hallucinate
- Tool-based: Mỗi lần chat phải gọi 3-5 tool để lấy context → latency tăng, token usage tăng, loop phức tạp hơn

# Key concepts to learn
- **System message priority**: LLM ưu tiên instruction trong system message hơn user message. Context block là system message → LLM luôn đọc.
- **Multiple system messages**: OpenAI API hỗ trợ nhiều system message, LLM sẽ merge chúng. Đây là pattern phổ biến để tách static rules khỏi dynamic context.
- **Fail-safe pattern trong AI pipeline**: Mọi external call (DB, service) trong context builder đều wrapped trong try/except. Context là optional enhancement, không phải hard requirement.

# Common mistakes
- Query quá nhiều data trong context block → vượt token limit, hoặc đẩy history quan trọng ra khỏi context window
- Không handle lỗi → một service lỗi làm crash toàn bộ chat
- Hardcode context format → khó maintain khi thêm field mới
- Đặt context block trước static prompt → LLM có thể ưu tiên data hơn rules (nguy hiểm với human-in-the-loop constraint)

# Small example
```python
# Before: HR chat không có context
messages = [
    {"role": "system", "content": "You are the AI Assistant for Vroom HR..."},
    {"role": "user", "content": "Có bao nhiêu CV đang chờ review?"},
]
# LLM phải gọi tool count_candidates_by_status → 1 tool call thêm

# After: HR chat có context block
messages = [
    {"role": "system", "content": "You are the AI Assistant for Vroom HR..."},
    {"role": "system", "content": "---\nPipeline: đang xem xét: 8\n---"},
    {"role": "user", "content": "Có bao nhiêu CV đang chờ review?"},
]
# LLM có thể trả lời ngay: "Có 8 ứng viên đang chờ review"
```

# How to think about this next time
- Context block là **enhancement layer**, không phải core logic. Luôn làm nó optional và fail-safe.
- Mỗi field trong context nên đến từ một service call độc lập → dễ test, dễ thay đổi
- "What does the LLM need to know before the user even asks?" → đó chính là context block
