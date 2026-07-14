# Task
Bổ sung provenance và audit quyết định cho Draft Action của AI Assistant theo issue #206.

# What I changed
- Thêm provenance có kiểu vào Draft Action và các Draft-Tool của HR/Employee.
- Thêm endpoint ghi nhận HR confirm/reject, chỉ lưu metadata redacted thay vì raw conversation.
- Frontend ghi nhận quyết định sau khi confirm hoặc khi reject.
- Bổ sung test provenance và cập nhật test UI.

# The real problem
LLM chỉ nên đề xuất. Hệ thống cần chứng minh proposal lấy dữ liệu từ scope nào, tool nào, đồng thời lưu được quyết định của HR mà không biến conversation thành dữ liệu audit mặc định.

# Why this solution
Provenance nằm ngay trong Draft Action nên đi cùng proposal tới UI và endpoint audit. Write endpoint vẫn được gọi ngoài LLM loop; audit chỉ nhận action type, scope, tool, version và candidate id đã redacted.

# Production shape
LLM gọi Read-Tool hoặc Draft-Tool. Backend tạo Draft Action có provenance. HR xem preview rồi UI gọi write endpoint thật. Sau kết quả, UI gọi draft-decision để audit confirm/reject. Không có database write-tool trong registry.

# Other possible approaches
1. Lưu toàn bộ conversation và replay khi audit — phù hợp hệ thống cần điều tra hội thoại đầy đủ.
2. Tạo bảng DraftAction riêng với lifecycle và snapshot — phù hợp khi draft cần tồn tại lâu, nhiều người review hoặc có expiry.

# Why I did not choose those alternatives
Conversation raw vi phạm mặc định privacy của issue. Bảng riêng lớn hơn nhu cầu hiện tại và dễ tạo thêm state machine trước khi domain cần; audit metadata đủ cho phase này.

# Key concepts to learn
Human-in-the-loop, provenance, capability boundary, redaction, audit decision, stateless chat.

# Common mistakes
- Gọi write endpoint từ tool loop.
- Ghi body email hoặc raw prompt vào audit.
- Tin provenance do client tự tạo mà không giới hạn endpoint.
- Gọi confirm là thành công trước khi write endpoint trả về thành công.

# Small example
`provenance = {"tool": "draft_interview_invitation", "scope": "recruitment", "candidate_id": "..."}`.

# How to think about this next time
Tách ba việc: đọc live data, tạo proposal, và thực thi sau xác nhận. Mỗi ranh giới phải có type, endpoint validation, và audit event riêng.
