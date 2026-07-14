# Task

Grilling và chốt domain model cho các khoảng trống/rủi ro trong snapshot Vroom HR.

# What I changed

- Cập nhật `CONTEXT.md` để `Onboarding` không còn mang trạng thái triển khai lỗi thời.
- Làm rõ điều kiện Employee trở thành active: task bắt buộc hoàn tất và đủ department, position, manager, start date.
- Cập nhật `README.md` để phân biệt Attendance, Payslip và payroll calculation engine.
- Ghi rõ các báo cáo trạng thái có ngày tháng là snapshot lịch sử, không phải nguồn sự thật hiện tại.
- Cập nhật ADR Google Workspace về `needs_relink`, Gmail cursor thuộc Organization Connection, bounded full sync sau `410` và conflict resolution sau `412`.
- Không thay đổi runtime code trong phiên này.

# The real problem

Vấn đề không chỉ là vài câu tài liệu cũ. Repository đang có nhiều boundary domain dễ bị hiểu sai:

- glossary trộn định nghĩa domain với trạng thái triển khai;
- `Payslip` có thể bị gọi nhầm là payroll engine;
- Google connection đã có singleton nhưng runtime legacy vẫn gắn ownership với `user_id`;
- Calendar migration cần phân biệt lifecycle của Interview với cờ cần relink;
- snapshot lịch sử dễ bị coi là trạng thái hiện tại;
- placeholder UI làm người dùng tưởng capability đã sẵn sàng.

# Why this solution

Giữ glossary cho thuật ngữ và invariant domain, giữ ADR cho trade-off kiến trúc, giữ README cho phạm vi capability công khai và giữ snapshot có ngày tháng cho lịch sử. Cách phân lớp này tránh dùng một tài liệu cho cả ba mục đích.

Google ownership được chốt theo hard cutover: token và cursor thuộc Organization Google Connection; HR chỉ là actor/audit subject. Calendar không fallback về `primary`; `410` không suy ra deletion từ việc event vắng mặt; `412` phải có quyết định rõ của HR.

# Production shape

Runtime production cần có các invariant sau:

- Gmail worker không còn nhận ownership runtime theo `user_id`.
- Gmail cursor là một cursor của Organization Google Connection và reconnect thiết lập baseline mới.
- Legacy grant bị revoke; connection cũ chuyển `reauthorization_required` và không được worker sử dụng.
- Calendar create/update/delete/sync dùng selected calendar bắt buộc.
- Interview giữ lifecycle `scheduled/completed/cancelled`; `needs_relink` là cờ repair riêng.
- Calendar `410` chạy bounded full sync; chỉ deletion rõ ràng mới hủy Interview.
- Calendar `412` tạo conflict; giữ Google hoặc ghi đè Vroom đều cần HR xác nhận và audit.
- Attendance và Payroll placeholder không xuất hiện như capability sẵn sàng; Employee Request và Payslip vẫn được công bố đúng phạm vi.
- Google migration, migration rollback và các invariant trên là release gate.

Các invariant runtime trên được chốt trong phiên nhưng chưa được triển khai trong phiên này.

# Other possible approaches

1. Giữ dual ownership theo HR và Organization trong giai đoạn chuyển tiếp.
2. Giữ `primary` làm fallback khi chưa chọn selected calendar.
3. Thêm `needs_relink` vào lifecycle status của Interview.
4. Xóa các snapshot tĩnh và chỉ sinh báo cáo live.
5. Xây payroll calculation engine cùng đợt với Payslip.

# Why I did not choose those alternatives

- Dual ownership duy trì rủi ro worker dùng nhầm grant và làm mơ hồ chủ sở hữu token.
- Fallback `primary` có thể ghi event vào lịch sai; thiếu selected calendar phải fail closed.
- Đưa `needs_relink` vào lifecycle làm lẫn vấn đề binding Calendar với vòng đời nghiệp vụ Interview.
- Chỉ dùng báo cáo live làm mất bằng chứng lịch sử; snapshot có ngày tháng phù hợp cho so sánh theo mốc.
- Gộp payroll engine vào Payslip làm tăng scope và tạo kỳ vọng sai về tính lương, thuế và phụ cấp.

# Key concepts to learn

- Ubiquitous language và ranh giới giữa glossary, ADR, README và roadmap.
- Organization singleton ownership so với HR actor/audit subject.
- Idempotency và baseline khi reconnect một nguồn đồng bộ.
- Optimistic concurrency với ETag và `412 Precondition Failed`.
- Bounded full sync sau `410 Gone`.
- Lifecycle state so với repair/attention flag.
- Payslip presentation so với payroll calculation engine.
- Snapshot bất biến và current source of truth.

# Common mistakes

- Ghi “module chưa active” chỉ vì một UI phụ còn placeholder.
- Gọi Payslip là payroll engine.
- Dùng `connected_by_user_id` như owner thay vì audit metadata.
- Dùng `primary` làm default vô hình.
- Đánh dấu Interview cancelled chỉ vì event không xuất hiện trong một bounded sync.
- Retry `412` tự động bằng ETag mới mà không tạo conflict cho HR.
- Đưa trạng thái migration/repair vào lifecycle domain.
- Sửa snapshot lịch sử tại chỗ rồi vẫn coi ngày file là mốc chính xác.

# Small example

Một Organization có Google Connection singleton và một Interview `scheduled`.

- HR reconnect: credential cũ bị xóa/revoke, connection thành `reauthorization_required`, Gmail cursor bị reset; Candidate và Interview history vẫn giữ.
- HR chọn lại calendar tuyển dụng: thao tác Calendar dùng đúng `selected_calendar_id`, không dùng `primary` ngầm.
- Google trả `412`: hệ thống tạo conflict; HR chọn giữ phiên bản Google hoặc xác nhận ghi đè từ Vroom.
- Google trả `410`: hệ thống xóa sync token và chạy bounded full sync; event chỉ bị hủy khi Google báo deletion rõ ràng.

# How to think about this next time

Trước khi sửa tài liệu hoặc code, hãy hỏi ba câu:

1. Thuật ngữ này mô tả domain bất biến hay trạng thái triển khai tạm thời?
2. Ai thực sự sở hữu dữ liệu/token/cursor, và ai chỉ thực hiện hành động hoặc được ghi audit?
3. Một trạng thái lỗi/repair có phải lifecycle state không, hay là cờ phụ cần xử lý?

Sau đó kiểm tra code và ADR để tìm invariant thực tế, chốt quyết định với scenario cụ thể, rồi ghi quyết định vào đúng loại tài liệu. Không dùng README, glossary hoặc snapshot để thay thế lẫn nhau.
