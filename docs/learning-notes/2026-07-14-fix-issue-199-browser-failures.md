# Task

Sửa các lỗi phát hiện khi dùng Playwright kiểm tra GitHub Issue #199: Candidate read/promotion trả 500, AI Assistant bị treo khi provider không khả dụng, và Employee Draft Action mở form nhưng không áp dụng dữ liệu.

# What I changed

- Giới hạn mọi query đọc `Candidate` bằng `load_only()` với các cột còn tồn tại trong bảng `candidates`.
- Khi tạo Candidate, dùng câu `INSERT` chỉ chứa cột hậu migration 054; promotion không còn ghi ba cột legacy đã bị xóa.
- Truyền `max_retries` từ `AssistantSettings` vào `AsyncOpenAI` thay vì bỏ qua cấu hình.
- Cấu hình Docker local để Assistant provider có host gateway, timeout 5 giây và không retry vô hạn.
- Thêm trạng thái lỗi và nút `Thử lại` trong `ChatInterface`.
- Sửa lifecycle mở request dialog để dữ liệu từ Employee Draft Action được áp dụng sau khi dialog mount.
- Thêm regression tests cho Candidate read/create projection, retry policy và Employee Draft Action prefill.

# The real problem

Migration 054 đã chuyển dữ liệu lịch phỏng vấn sang bảng `interviews` và xóa ba cột legacy khỏi `candidates`, nhưng ORM `Candidate` vẫn giữ các field cũ. Query `select(Candidate)` vì vậy sinh SQL tham chiếu cột không còn tồn tại và trả HTTP 500.

Lỗi tương tự xuất hiện ở promotion: ORM insert mặc định cũng đưa ba cột đã xóa vào `INSERT`. Vì vậy chỉ sửa candidate listing chưa đủ; mọi read projection và create statement đều phải khớp schema runtime.

AI client có setting `max_retries`, nhưng constructor không truyền setting này cho OpenAI SDK. SDK tự dùng retry mặc định và timeout dài, khiến frontend proxy bị socket hang up trước khi nhận được lỗi có cấu trúc.

Employee Assistant đã trả Draft Action đúng, nhưng callback mở dialog chạy trước khi `ref` của dialog được mount. Effect không chạy lại khi `ref.current` thay đổi, nên form mở với giá trị mặc định.

# Why this solution

Candidate read dùng projection chứa đủ dữ liệu nghiệp vụ còn tồn tại. Candidate create dùng SQLAlchemy `insert(Candidate).values(...)` sau khi loại ba field legacy, nên vẫn giữ transaction hiện tại mà không ghi vào cột đã drop.

Assistant vẫn giữ human-in-the-loop và không giả lập câu trả lời khi provider hỏng. Lỗi được trả về dạng 502, thời gian chờ được giới hạn, và frontend cho phép HR thử lại rõ ràng. Employee Draft Action chỉ prefill form; write endpoint vẫn chỉ được gọi sau thao tác xác nhận riêng của Employee.

# Production shape

- Schema runtime là nguồn sự thật; ORM read projection không được tham chiếu cột đã bị drop.
- Provider timeout/retry phải là cấu hình có giới hạn và được chuyển đầy đủ tới SDK.
- Provider outage không được biến thành `other`, dữ liệu giả hoặc write action.
- UI phải giữ nội dung user message và cung cấp hành động retry sau lỗi tạm thời.
- Candidate promotion phải idempotent và chỉ tạo Candidate sau hành động HR rõ ràng.
- Draft Action chỉ mang dữ liệu đề xuất; dialog mount/prefill và write confirmation là hai bước riêng.

# Other possible approaches

1. Tạo migration để thêm lại ba cột vào `candidates`. Phù hợp khi cần rollback hoàn toàn về legacy scheduling contract.
2. Xóa hẳn ba field khỏi `Candidate` và migrate toàn bộ service sang `Interview`. Phù hợp cho clean cutover lớn, khi đã cập nhật mọi caller scheduling.
3. Tạo entity read-model riêng cho candidate listing. Phù hợp khi cần projection ổn định, cache hoặc query tối ưu độc lập với aggregate Candidate.

# Why I did not choose those alternatives

- Thêm lại cột đi ngược migration 054, tạo hai nguồn sự thật giữa `candidates` và `interviews`, và che giấu lỗi schema.
- Xóa field ngay lập tức có blast radius lớn vì nhiều flow lịch phỏng vấn legacy vẫn đọc chúng.
- Read-model riêng là thay đổi kiến trúc lớn hơn mức cần thiết để sửa lỗi 500 hiện tại; `load_only()` là seam nhỏ và an toàn hơn.

# Key concepts to learn

- SQLAlchemy ORM mapper có thể giữ field legacy dù database đã thay đổi.
- `load_only()` giới hạn SELECT projection nhưng vẫn trả entity cho service layer.
- SDK retry mặc định có thể khác retry setting của application.
- ORM `INSERT` cũng phải được kiểm tra sau migration; giới hạn `SELECT` không bảo vệ write path.
- React effect phụ thuộc vào state render, không nên phụ thuộc vào thay đổi của `ref.current`.
- HTTP 502, timeout bounded và retry UI là ba lớp khác nhau của provider failure handling.

# Common mistakes

- Chỉ kiểm tra model Python mà không kiểm tra schema database thực tế.
- Dùng `select(Entity)` sau migration drop column mà không giới hạn projection.
- Khai báo `max_retries` trong settings nhưng quên truyền vào client SDK.
- Xóa input sau lỗi khiến người dùng phải nhập lại câu hỏi.
- Biến provider outage thành kết quả nghiệp vụ hợp lệ như `other`.
- Giả định sửa read projection sẽ tự sửa cả create/update statement.
- Gọi imperative dialog ref trước khi component chứa ref được mount.

# Small example

```python
statement = select(Candidate).options(
    load_only(
        Candidate.id,
        Candidate.name,
        Candidate.email,
        Candidate.status,
        Candidate.created_at,
    )
)
```

```python
values = candidate.model_dump(
    exclude={"calendar_event_id", "interview_start_at", "interview_timezone"}
)
await session.execute(insert(Candidate).values(values))
```

```python
AsyncOpenAI(
    base_url=settings.base_url,
    timeout=settings.timeout_seconds,
    max_retries=settings.max_retries,
)
```

# How to think about this next time

Khi browser thấy HTTP 500, truy từ UI đến proxy, route, service, repository rồi chạy query trực tiếp trên database. Sau mỗi migration đổi schema, kiểm tra các ORM model và các query `select(Entity)`. Với provider AI, kiểm tra cả endpoint reachability, timeout thực tế, SDK retry mặc định và hành vi UI khi lỗi.
Luôn smoke-test cả read và write tương ứng trên database đã chạy migration thật. Với Draft Action, kiểm tra ba mốc độc lập: payload typed từ Assistant, form được prefill đúng, và database chưa đổi trước khi người dùng xác nhận.
