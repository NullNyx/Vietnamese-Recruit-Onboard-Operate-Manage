# Task

Triển khai Employee Assistant self-service có phạm vi dữ liệu theo Employee active.

# What I changed

- Thêm Read-Tool `get_my_leave_balance`, chỉ đọc các leave request của Employee đang đăng nhập.
- Tính snapshot gồm entitlement mặc định 12 ngày, ngày đã duyệt, ngày chờ duyệt và ngày còn lại; kèm `as_of` để thể hiện freshness.
- Registry từ chối rõ ràng các tool truy cập Candidate, aggregate hoặc dữ liệu Employee khác.
- Bổ sung `assistant_type` trong provenance để phân biệt `employee_assistant` và `ai_assistant`.
- Bổ sung test boundary cho leave balance, scope refusal và no-write.

# The real problem

LLM có thể chọn tên tool hoặc tham số ngoài ý định hội thoại. Ranh giới an toàn phải nằm ở service/tool registry, không chỉ ở system prompt. Employee ID phải được tiêm từ session và không được nhận từ LLM.

# Why this solution

Registry giữ employee ID bất biến, chỉ expose tool self-service, và trả refusal trước khi dispatch tool lạ. Draft request chỉ tạo Draft Action; không gọi service ghi dữ liệu. `as_of` giúp câu trả lời live data không bị hiểu nhầm là dữ liệu tĩnh.

# Production shape

Entitlement hiện chưa có bảng cấu hình trong module Employee Request nên dùng policy mặc định 12 ngày. Khi có entitlement policy, registry nên nhận policy service thay vì hard-code hằng số. Endpoint submit thật vẫn nằm ngoài LLM loop và chỉ chạy sau xác nhận UI.

# Other possible approaches

1. Tạo bảng entitlement theo Employee/năm để lưu quota và carry-over.
2. Tính balance trong một LeaveBalance application service dùng chung cho API và Assistant.

# Why I did not choose those alternatives

Bảng entitlement cần migration và policy nghiệp vụ chưa tồn tại trong issue này. Service dùng chung là hướng tốt hơn về dài hạn nhưng chưa có contract hiện hữu; thay đổi tối thiểu ở registry vẫn đáp ứng boundary và không mở rộng write surface.

# Key concepts to learn

- Capability-based tool registry.
- Server-side authorization scope injection.
- Draft-only human-in-the-loop.
- Freshness metadata và audit provenance.

# Common mistakes

- Tin `employee_id` do LLM gửi.
- Cho LLM gọi endpoint submit trực tiếp.
- Trả lỗi nội bộ hoặc PII vào conversation.
- Dùng cùng provenance cho HR Assistant và Employee Assistant.

# Small example

`get_my_leave_balance({"employee_id": "employee-khac"})` vẫn gọi `list_my_leaves(authenticated_employee_id)`. `search_candidates(...)` trả `scope_denied` và không dispatch service nào.

# How to think about this next time

Xác định capability được phép trước, gắn scope vào dependency đã xác thực, rồi kiểm thử ngay tại registry boundary. Prompt chỉ hướng dẫn; registry mới là enforcement point.
