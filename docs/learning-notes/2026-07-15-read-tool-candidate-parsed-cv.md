# Task
Thêm Read-Tool `get_candidate_parsed_cv` vào HR Assistant — cho phép LLM đọc dữ liệu CV đã được AI Automation parse.

# What I changed
- **`tools.py`**: Thêm `ToolDefinition` `get_candidate_parsed_cv` (kind=READ, param `candidate_id`)
- **`tool_registry.py`**: Thêm handler `_get_candidate_parsed_cv` — validate UUID, gọi `CandidateService.get_candidate()`, trả về structured JSON
- **3 test files**: Cập nhật hardcoded tool counts (5→6 tools, 3→4 Read-Tools, thêm tool name vào expected sets)
- **`test_tool_registry.py`**: Thêm 4 tests cho tool mới

# The real problem
HR Assistant không đọc được nội dung CV. Khi HR hỏi "tóm tắt CV của ứng viên X", LLM chỉ biết tên/email/status từ `search_candidates` — không có skills, experience, education để trả lời. Draft email cũng không cá nhân hóa được vì không có context từ CV.

# Why this solution
- **Pattern nhất quán**: Giống hệt các Read-Tool hiện có (`search_candidates`, `count_candidates_by_status`) — chỉ khác là gọi `get_candidate()` thay vì `list_candidates()`
- **Dùng service có sẵn**: `CandidateService.get_candidate()` trả về `CandidateDetail` với `candidate` entity chứa `skills`, `experience`, `education`, `summary`, `parsed_cv_json` — không cần thêm service/repo mới
- **Không trả về presigned URLs**: CV documents được generate presigned URL nhưng tool này chỉ trả về parsed structured data — giữ cho LLM context gọn, không tốn token cho URLs
- **Error handling đầy đủ**: Invalid UUID, missing param, candidate not found — mỗi case có error message rõ ràng

# Production shape
```json
{
  "candidate_id": "uuid",
  "name": "Nguyễn Văn A",
  "email": "a@example.com",
  "phone": "0123456789",
  "skills": ["Python", "FastAPI"],
  "experience": [{"company": "FPT", "role": "Dev"}],
  "education": [{"school": "Bách Khoa", "degree": "Kỹ sư"}],
  "summary": "5 năm kinh nghiệm backend",
  "parsed_cv_json": { ... full parsed CV ... },
  "confidence_score": 0.95,
  "status": "reviewing"
}
```

# Other possible approaches
1. **Trả về toàn bộ CandidateDetail (bao gồm CV documents + presigned URLs)**: Thừa thông tin cho LLM, tốn token, URLs có thể expired
2. **Tool riêng cho từng phần CV (get_candidate_skills, get_candidate_experience...)**: Quá nhiều tool, LLM phải gọi nhiều lần → tăng latency
3. **Merge vào search_candidates (trả về thêm CV summary)**: Làm search_candidates nặng hơn, phá vỡ single responsibility

# Why I did not choose those alternatives
- Full CandidateDetail: presigned URLs không cần thiết cho LLM, chỉ cần cho UI
- Tách nhỏ tools: Vi phạm nguyên tắc "tool nên self-contained" — LLM phải orchestrate nhiều call không cần thiết
- Merge vào search: Search nên nhẹ (tên, email, status), CV detail nên là tool riêng — tách biệt concern

# Key concepts to learn
- Tool nên trả về **đủ context để LLM trả lời**, không thừa không thiếu
- Read-Tool pattern: validate param → gọi service → format JSON → return
- `parsed_cv_json` là raw data từ AI Automation pipeline — có thể chứa bất kỳ field nào, LLM có thể tự explore

# Common mistakes
- Trả về quá nhiều data (như presigned URLs) — LLM không cần, tốn token
- Không validate UUID trước khi gọi service — có thể crash với input xấu
- Quên cập nhật test count assertions khi thêm tool mới

# Small example
```
HR: "Cho tôi xem CV của Nguyễn Văn A"
→ LLM gọi search_candidates(query="Nguyễn Văn A") → có candidate_id
→ LLM gọi get_candidate_parsed_cv(candidate_id) → có skills, experience
→ LLM trả lời: "Nguyễn Văn A có 5 năm kinh nghiệm backend, thành thạo Python và FastAPI..."
```

# How to think about this next time
- Mỗi Read-Tool nên map 1-1 với một câu hỏi nghiệp vụ HR thường hỏi
- "HR hỏi gì về CV?" → đó chính là các field tool nên trả về
- Tool đủ nhỏ để LLM không bị overload, đủ lớn để không phải gọi nhiều tool cho một câu hỏi
