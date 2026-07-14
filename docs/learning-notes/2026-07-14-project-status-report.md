# Task — Nhiệm vụ

Tạo báo cáo snapshot bằng tiếng Việt về tình hình project Vroom HR, bao gồm tính năng, API, UI và logic luồng hoạt động.

# What I changed — Những gì đã thay đổi

- Tạo `docs/project-status-2026-07-14.md`.
- Tổng hợp trạng thái từ router được wiring trong `backend/src/main.py`, module backend, trang frontend, Alembic migration, test và ADR.
- Thêm bảng feature matrix, bảng API theo module, flow tuyển dụng/onboarding/ESS và bảng khoảng trống/rủi ro.
- Ghi rõ những chỗ tài liệu cũ lệch với code, đặc biệt attendance/payroll và trạng thái Onboarding.

# The real problem — Vấn đề thực sự

Project đã có nhiều code chạy thật nhưng thông tin trạng thái nằm rải rác trong router, service, worker, frontend và test. README có một số mô tả cũ, còn CONTEXT mô tả Onboarding như mắt xích chưa có dù backend đã có event consumer. Vì vậy người đọc dễ nhầm giữa “có module trong source”, “đã có API”, “đã có UI” và “đã sẵn sàng production”.

# Why this solution — Tại sao chọn giải pháp này

Báo cáo dùng snapshot có ngày thay vì tuyên bố trạng thái vĩnh viễn. Mỗi tính năng được tổng hợp theo bốn chiều: logic nghiệp vụ, bề mặt API/UI, trạng thái triển khai và rủi ro còn lại. Cách này giữ được toàn cảnh mà vẫn chỉ ra rõ phần backend đã có nhưng frontend còn placeholder, hoặc phần Google integration đang chuyển đổi ownership.

# Production shape — Hình dạng production

- Một deployment phục vụ một Organization.
- FastAPI đăng ký các router Identity, Admin, Employee, Gmail, Recruitment, Onboarding, Attendance, Employee Request, Payslip, Assistant và Runtime.
- Redis phục vụ ARQ worker, cursor/heartbeat và retry; PostgreSQL lưu domain state; MinIO lưu tài liệu/CV.
- Backbone Flow đi từ email đến Job Application, Candidate, Interview, accept, Onboarding và Employee active.
- AI Automation là pipeline nền; AI Assistant chỉ có Read-Tool/Draft-Tool và luôn giữ human-in-the-loop.
- Production còn cần hoàn tất Google ownership migration, kiểm tra secrets, smoke test tích hợp và xử lý các UI placeholder.

# Other possible approaches — Các hướng tiếp cận khả thi khác

1. **Chỉ viết một bảng module ngắn trong README.** Phù hợp khi project nhỏ và toàn bộ logic nằm ở vài module ổn định.
2. **Sinh báo cáo tự động từ OpenAPI rồi bổ sung thủ công.** Phù hợp khi cần inventory endpoint chính xác, cập nhật thường xuyên và backend là nguồn sự thật duy nhất.
3. **Dùng dashboard trạng thái live trong ứng dụng.** Phù hợp khi team cần xem health/telemetry theo thời gian thực thay vì đọc tài liệu snapshot.

# Why I did not choose those alternatives — Tại sao không chọn các giải pháp thay thế đó

- Bảng README ngắn sẽ bỏ sót worker, domain invariant, frontend placeholder và các boundary AI an toàn.
- OpenAPI không thể hiện đầy đủ những trang UI chưa triển khai, logic event queue, ADR hay phần migration đang chuyển đổi.
- Dashboard live cần thêm code, dữ liệu vận hành và maintenance; yêu cầu hiện tại chỉ cần một file Markdown tiếng Việt để tổng hợp project.
- Vì vậy chọn báo cáo snapshot có nguồn tham chiếu và phần risk/gap rõ ràng; sau này có thể dùng nó làm contract cho một generator live.

# Key concepts to learn — Các khái niệm chính cần học

- Phân biệt Organization, User, HR, Employee, Employee Account và Employee Self-Service.
- Phân biệt Job Application với Candidate; AI không được tự promote Candidate khi còn mơ hồ.
- Phân biệt Interview với Candidate pipeline; lịch Calendar không tự đổi status nghiệp vụ.
- Event-driven onboarding: `candidate_accepted` → ARQ consumer → Employee inactive → checklist → Employee active.
- Idempotency, retry, cursor, ETag và conflict khi tích hợp Gmail/Calendar.
- Human-in-the-loop: Draft-Tool chỉ trả proposal; frontend gọi write endpoint sau khi người dùng confirm.
- Snapshot status khác với production readiness: có route/code không đồng nghĩa đã có UI hoàn chỉnh hoặc đã smoke test production.

# Common mistakes — Các lỗi thường gặp

- Dùng README cũ làm nguồn duy nhất và kết luận Attendance/Payslip không active.
- Gọi Job Application là Candidate hoặc coi có CV mới là đủ để tạo Candidate.
- Gọi Employee inactive là Employee active hoặc cấp Employee Account trước khi onboarding xong.
- Cho LLM write-tool vì prompt nói “chỉ được gửi khi confidence cao”.
- Gộp Interview vào một calendar field trên Candidate và làm mất lịch sử reschedule/cancel.
- Gọi Payslip CRUD là payroll calculation engine.
- Đánh dấu tính năng “đã xong” chỉ vì có backend route trong khi frontend còn trang placeholder.
- Không ghi ngày snapshot, khiến báo cáo tĩnh bị hiểu nhầm là trạng thái live.

# Small example — Ví dụ nhỏ

Một email ứng tuyển có thể đi qua các trạng thái sau:

```text
Gmail message
  → AI intent = job_application
  → Job Application (chưa phải Candidate)
  → HR xác nhận đủ thông tin
  → Candidate = new
  → HR review / tạo Interview
  → HR accept
  → event candidate_accepted
  → Employee inactive + checklist
  → hoàn tất task cuối
  → Employee active + Employee Account
```

Nếu AI không chắc intent hoặc application thiếu dữ liệu, item phải ở Recruitment Inbox để HR xử lý thay vì tạo Candidate ngay.

# How to think about this next time — Cách suy nghĩ về điều này lần sau

1. Bắt đầu từ wiring thật của application, không bắt đầu từ menu hoặc README.
2. Với mỗi module, kiểm tra đủ bốn lớp: route, service/domain, UI và test/migration.
3. Vẽ flow theo event và boundary quyền, đặc biệt ở các điểm AI, HR approval và Employee self-service.
4. Tách rõ “đã có code”, “đã có UI”, “đã được kiểm thử” và “đã sẵn sàng production”.
5. Ghi các điểm lệch tài liệu thành risk cụ thể thay vì âm thầm suy đoán phiên bản nào đúng.
6. Đặt ngày snapshot và nguồn tham chiếu để lần cập nhật sau có thể so sánh thay đổi.
