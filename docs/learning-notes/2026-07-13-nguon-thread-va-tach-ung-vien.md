# Task

Triển khai issue #185 để HR xử lý referral, agency, email nhiều ứng viên, email bổ sung cùng Gmail thread và đề xuất liên kết khác thread.

# What I changed

- Tách applicant identity khỏi sender identity và lưu lại evidence/source hints trên Job Application.
- Dùng Gmail thread làm ranh giới liên kết mặc định; message bổ sung cùng thread được thêm vào `message_references` thay vì tạo duplicate.
- Đưa email có bằng chứng nhiều ứng viên vào Recruitment Inbox dù confidence cao, để HR tách đúng cardinality.
- Thêm thao tác split tạo một Job Application cho mỗi người nhưng giữ chung source email reference.
- Thêm Link Proposal với trạng thái `pending → confirmed/rejected`; khác thread không thay đổi Job Application trước khi HR xác nhận.
- Thêm migration 062, API, UI và journey tests cho split và cross-thread confirmation.

# The real problem

Vấn đề không chỉ là phân loại email. Một email có sender, một hay nhiều applicant, một Gmail thread và có thể liên quan đến nhiều Job Opening. Nếu dùng `gmail_message_id` như khóa duy nhất của Job Application hoặc dùng sender làm applicant, hệ thống làm sai cardinality và trộn provenance với identity.

# Why this solution

Thiết kế giữ ba quyết định độc lập:

1. Routing intent quyết định email có đi vào recruitment flow hay không.
2. Source/evidence mô tả email đến từ direct, referral hay agency.
3. HR quyết định cardinality và identity khi cần split/link.

Same-thread linking được tự động vì Gmail thread là ranh giới đã được ADR 0004 chấp nhận. Cross-thread link được biểu diễn bằng record proposal bất hoạt, nên safety không phụ thuộc vào convention ở frontend.

# Production shape

- `job_applications.gmail_message_id` là index không unique để một source tạo nhiều application.
- `message_references` lưu các message đã liên kết và loại liên kết.
- `job_application_link_proposals` lưu target, người đề xuất, quyết định và người resolve.
- Recruitment Inbox là surface HR cho source cần split hoặc link confirmation.
- Mọi thao tác split/link giữ audit metadata và không tạo Candidate.

# Other possible approaches

1. Tạo bảng nối chuẩn hóa `job_application_messages` thay cho JSON `message_references`.
2. Tự động merge khác thread bằng applicant email hoặc sender email.
3. Luôn tạo một Job Application trước, rồi merge/delete khi HR xác nhận.

# Why I did not choose those alternatives

- Bảng nối chuẩn hóa phù hợp khi cần query/report theo từng message ở quy mô lớn. Với scope hiện tại, JSON reference giữ migration và interface nhỏ hơn; nên chuyển sang bảng nối khi message-level querying trở thành nhu cầu production rõ ràng.
- Auto-merge khác thread chỉ phù hợp khi có identity resolution đáng tin cậy và false merge gần như bằng không. Hiện sender có thể là agency/referrer và một người có thể apply nhiều Job Opening, nên cách này nguy hiểm.
- Tạo rồi merge/delete phù hợp với hệ thống có lifecycle `merged` hoàn chỉnh. Domain hiện chưa có lifecycle đó; xóa hoặc merge record tạm sẽ làm audit và idempotency phức tạp hơn.

# Key concepts to learn

- Routing intent khác provenance và khác applicant identity.
- Gmail thread là linking boundary, không phải sender email.
- Một source email có thể có cardinality 1:N với Job Application.
- Proposal bất hoạt là cách biểu diễn human-in-the-loop có tính cấu trúc.
- Unique constraint phải phản ánh domain cardinality, không chỉ nhu cầu idempotency ban đầu.

# Common mistakes

- Copy sender vào applicant cho referral/agency.
- Dùng sender email để auto-merge khác thread.
- Giữ unique constraint trên source message rồi cố split ở application layer.
- Cho nút “link” ghi thẳng dữ liệu trước khi HR xác nhận.
- Tạo một Job Application cho email nhiều người và làm mất các applicant còn lại.

# Small example

Agency gửi một email chứa CV của An và Bình. HR chọn source `agency`, nhập hai applicant rồi split. Hệ thống tạo hai Job Application khác ID nhưng cùng `source_email_message_id`. Một email bổ sung trong cùng thread được thêm vào cả hai application. Nếu email bổ sung nằm ở thread khác, hệ thống chỉ tạo Link Proposal; Job Application chưa đổi cho tới khi HR bấm xác nhận.

# How to think about this next time

Trước khi đặt unique key hoặc viết deduplication, hãy viết rõ cardinality giữa source, message, thread, applicant và business record. Sau đó tách quyết định an toàn có thể tự động hóa khỏi quyết định mơ hồ cần người xác nhận, và biểu diễn sự khác biệt đó trong persistence thay vì chỉ trong UI.
