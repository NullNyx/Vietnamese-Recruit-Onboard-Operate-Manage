    # Task
    Thêm 2 Read-Tool mới vào HR Assistant:
    - **`list_interviews_for_candidate`** (#229): Cho phép LLM đọc danh sách phỏng vấn của một ứng viên
    - **`get_onboarding_task_details`** (#230): Cho phép LLM đọc chi tiết task trong một onboarding process
    
    # What I changed
    - **`tools.py`**: Thêm 2 `ToolDefinition` — `list_interviews_for_candidate` (kind=READ, param `candidate_id`) và `get_onboarding_task_details` (kind=READ, param `onboarding_process_id`)
    - **`candidate_service.py`**: Thêm public method `list_interviews_for_candidate(candidate_id)` — query `Interview` theo `candidate_id`, order by `start_at` descending, trả về list of dicts với `scheduled_time`, `status`, `location`, `notes`
    - **`tool_registry.py`**: Thêm 2 handlers (`_list_interviews_for_candidate`, `_get_onboarding_task_details`) + đăng ký trong `handlers` dict
    - **`test_tool_registry.py`**: Thêm 8 tests (4 cho mỗi tool) — success path, missing param, invalid UUID, nonexistent entity
    
    # The real problem
    HR Assistant có `search_candidates` nhưng không trả lời được:
    - "Ứng viên A có lịch phỏng vấn nào không?" — không có tool nào đọc interviews
    - "Onboarding của B tới đâu rồi?" — chỉ có `list_in_progress_onboarding` (tổng quan list), không xem được chi tiết task của một process cụ thể
    
    # Why this solution
    
    ## list_interviews_for_candidate
    - **Không có InterviewService riêng**: Interview CRUD nằm trong `CandidateService` (từ GH #154). Methods như `_get_scheduled_interview()` đã query direct bằng `self._session.execute()`. Pattern này dùng được cho read-only query.
    - **Thêm public method**: `list_interviews_for_candidate()` query `select(Interview).where(candidate_id=...)`, trả về dict thay vì entity — tránh leak internal domain objects ra Assistant layer
    - **Location field**: Interview entity có `meeting_link` (ưu tiên) và `remote_location` (fallback) — gộp thành `location` cho LLM dễ xử lý
    - **Notes field**: Chưa có trong Interview entity → trả về `None` + comment `# not yet modelled`
    
    ## get_onboarding_task_details
    - **Dùng `OnboardingService.get_process()` có sẵn**: Service method này đã trả về `ProcessDetail` với `tasks: list[ProcessTaskDetail]` — mỗi task có `id`, `name`, `status`, `order_index`, `completed_at`, `completed_by_name`
    - **due_date/assigned_to**: Chưa có trong `OnboardingTask` entity → trả về `None`
    - **is_overdue**: Luôn `False` khi `due_date` không có — sẽ implement đúng khi model có `due_date`
    
    # Production shape
    
    ## list_interviews_for_candidate
    ```json
    {
      "interviews": [
        {
          "id": "uuid",
          "scheduled_time": "2026-07-20T09:00:00+07:00",
          "end_time": "2026-07-20T10:00:00+07:00",
          "status": "scheduled",
          "round_name": "Vòng 1",
          "location": "Phòng họp 1",
          "meeting_mode": "in_person",
          "notes": null,
          "timezone": "Asia/Ho_Chi_Minh"
        }
      ],
      "total": 1
    }
    ```
    
    ## get_onboarding_task_details
    ```json
    {
      "process_id": "uuid",
      "status": "in_progress",
      "completed_count": 0,
      "total_count": 4,
      "tasks": [
        {
          "id": "uuid",
          "name": "Cung cấp giấy tờ",
          "status": "pending",
          "order_index": 0,
          "due_date": null,
          "is_overdue": false,
          "assigned_to": null,
          "completed_at": null,
          "completed_by_name": null
        }
      ]
    }
    ```
    
    # Other possible approaches
    
    1. **Tạo InterviewService riêng**: Quá heavy — chỉ cần 1 query, không cần full service layer
    2. **Dùng raw SQLAlchemy session trong ToolRegistry**: Phá vỡ ADR-0004 (one-way dependency), Assistant không nên biết về DB schema
    3. **Tách tool thành nhiều tool nhỏ (get_task_due_date, get_task_assigned_to...)**: Quá nhiều tool, LLM phải gọi nhiều lần
    4. **Merge vào list_in_progress_onboarding (mở rộng response với task details)**: Làm tool cũ nặng hơn, vi phạm SRP
    
    # Why I did not choose those alternatives
    
    - InterviewService: Assistant chỉ gọi 1 read method, không cần DI riêng. Method trong CandidateService đủ
    - Raw Session: Assistant đã inject CandidateService (có session) → query qua CandidateService là đúng seam
    - Tách nhỏ: `get_onboarding_task_details` trả về toàn bộ task list trong 1 call — LLM có đủ context để trả lời sau 1 lần gọi tool
    - Merge vào existing tool: `list_in_progress_onboarding` return list, không phải detail. Tách biệt list riêng, detail riêng
    
    # Key concepts to learn
    
    - Interview entity dùng `start_at`/`end_at` (datetime với timezone) → trả về `.isoformat()` cho LLM
    - Location có thể từ `meeting_link` (Google Meet) hoặc `remote_location` (địa điểm vật lý) — xử lý fallback đúng
    - OnboardingTask **chưa có** `due_date`/`assigned_to` — entity model cần mở rộng sau này. Tool trả về `null` + comment để document gap
    - `is_overdue` là derived field (tính từ `due_date` vs `now`) — cần được implement khi model có `due_date`
    - Pattern: tool handler → service method → ORM query, giữ assistant layer không biết về SQL
    
    # Common mistakes
    
    - Trả về entity object thay vì dict → risk leak internal state service ra response
    - Không handle trường hợp interview không có location (cả `meeting_link` và `remote_location` đều None) → location phải fallback về None
    - Quên rằng `get_process()` có thể raise `OnboardingProcessNotFoundError` — handler phải catch exception và trả về error message
    - is_overdue tính theo timezone của process, không phải timezone của HR
    
    # Small example
    
    ```
    HR: "Cho tôi xem lịch phỏng vấn của Nguyễn Văn A"
    → LLM gọi search_candidates(query="Nguyễn Văn A") → có candidate_id
    → LLM gọi list_interviews_for_candidate(candidate_id) → có interviews
    → LLM trả lời: "Nguyễn Văn A có 1 buổi phỏng vấn Vòng 1 vào 20/07/2026 lúc 09:00 tại Phòng họp 1"
    
    HR: "Onboarding của Nguyễn Văn B tới đâu rồi?"
    → LLM gọi list_in_progress_onboarding() → có process_id
    → LLM gọi get_onboarding_task_details(onboarding_process_id=...) → có tasks
    → LLM trả lời: "Đã hoàn thành 2/4 tasks. Còn thiếu: Cung cấp giấy tờ, Ký hợp đồng"
    ```
    
    # How to think about this next time
    
    - Mỗi entity (Interview, OnboardingTask) nên có 1 tool để đọc — đủ để LLM trả lời câu hỏi HR hay hỏi
    - Nếu entity chưa có field mà tool cần (due_date), trả về null + comment để document gap → dễ dàng implement sau
    - Derived fields (is_overdue) nên tính ở handler layer, không push xuống service — service stateless, handler tính toán presentation logic
    - Khi 1 service method (`get_process()`) trả về đủ data cho tool → không cần tạo method mới, chỉ cần mapping ở handler
