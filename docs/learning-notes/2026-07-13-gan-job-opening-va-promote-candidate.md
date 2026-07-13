# Task

Triển khai issue #186: cho HR gán Job Application vào tối đa một Job Opening và promote thành Candidate qua action có xác thực.

# What I changed

- Thêm migration liên kết duy nhất `job_applications.candidate_id` với `candidates.id`.
- Tách `JobApplicationDecisionService` dành riêng cho quyết định của HR khỏi service ingestion của AI Automation.
- Thêm API HR-only để gán/bỏ gán Job Opening và promote Candidate idempotent.
- Khóa Job Application khi ghi, commit transaction, lưu `audit_history`, và giữ liên kết Candidate.
- Thêm UI tiếp tục flow sau khi split: chọn Job Opening hoặc để trống, chỉnh danh tính và promote.
- Thêm test service, API authorization/idempotency, API client và UI journey.

# The real problem

Ranh giới quan trọng không phải chỉ là tạo Candidate. Hệ thống phải bảo đảm quyết định đưa một Job Application vào Candidate pipeline chỉ đến từ HR, không bị AI Automation gọi nhầm, không tạo Candidate trùng khi request lặp hoặc chạy đồng thời, và vẫn truy vết được nguồn Job Application.

# Why this solution

Promotion được đặt trong service riêng mà classifier không nhận được. API kiểm tra role HR trước khi gọi service. Row lock tuần tự hóa hai request promotion trên cùng Job Application; `candidate_id` duy nhất và trạng thái `promoted` giữ idempotency ở persistence. UI chỉ gọi public API, nên test journey không phụ thuộc implementation nội bộ.

# Production shape

- `POST /api/recruitment/job-applications/{id}/assignment`
- `POST /api/recruitment/job-applications/{id}/promote`
- `JobApplicationDecisionService` là write boundary của HR.
- `JobApplicationService` chỉ ingestion và không có method assignment/promotion.
- `job_applications.candidate_id` là nullable, unique FK.
- Sau split trong Recruitment Inbox, HR có thể chọn một Job Opening đang open hoặc để chưa xác định, rồi promote.

# Other possible approaches

1. Đặt promotion trực tiếp trong `JobApplicationService` đang dùng bởi AI ingestion.
2. Dùng idempotency key riêng cho mỗi HTTP request thay vì khóa Job Application và lưu `candidate_id`.
3. Tự động tạo Candidate ngay khi classifier đủ confidence.

# Why I did not choose those alternatives

1. Service dùng chung làm AI Automation nhìn thấy interface promotion, phá ranh giới human-in-the-loop. Cách này chỉ phù hợp nếu toàn bộ caller đều là trusted human command, điều không đúng ở đây.
2. Idempotency key phù hợp khi cùng một command có nhiều aggregate hoặc cần replay theo client key. Ở đây aggregate tự nhiên là Job Application; row lock và Candidate link đơn giản hơn và còn xử lý concurrent request.
3. Auto-promotion giảm thao tác HR nhưng làm dữ liệu AI chưa chắc chắn đi thẳng vào Candidate pipeline, trái ADR 0004 và spec.

# Key concepts to learn

- Human-in-the-loop boundary nên được thể hiện bằng interface/module, không chỉ comment hoặc role convention.
- Idempotency cần cả lookup durable và kiểm soát concurrency.
- Nullable FK biểu diễn Job Application chưa gán Job Opening; unique FK biểu diễn tối đa một Candidate được promote.
- UI journey nên mock public API boundary và thao tác qua control có accessible label.

# Common mistakes

- Chỉ flush mà quên commit nên API trả 200 nhưng dữ liệu bị rollback khi session đóng.
- Kiểm tra idempotency mà không lock row, khiến hai request đồng thời cùng tạo Candidate.
- Cho phép đổi Job Opening sau promotion làm Job Application và Candidate lệch nhau.
- Đưa promotion method vào ingestion service, vô tình cấp interface cho automation.
- Deduplicate Candidate theo email, làm mất hai application độc lập của cùng người cho hai Job Opening.

# Small example

```text
Job Application A (a@example.com, Opening X) -> Candidate A
Job Application B (a@example.com, Opening Y) -> Candidate B

POST promote A lần 2 -> trả lại Candidate A, không tạo Candidate mới.
```

# How to think about this next time

1. Xác định ai được phép ra quyết định domain và cấp cho họ interface riêng.
2. Chọn aggregate làm idempotency boundary.
3. Viết test public API cho auth, replay và các trạng thái terminal.
4. Kiểm tra transaction thật: lock, flush, commit và constraint database.
5. Kết nối UI qua public API, rồi test hành trình người dùng thay vì state nội bộ.
