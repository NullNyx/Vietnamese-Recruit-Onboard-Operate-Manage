# Task

Hoàn tất expand–contract cho routing intent tuyển dụng: migration dữ liệu legacy `cv` chưa tạo Candidate sang Job Application, chuyển consumer và producer còn lại sang `job_application`, rồi loại `cv` khỏi contract đang hoạt động.

# What I changed

- Thêm migration `065` tạo Job Application cho email legacy `cv` chưa có Candidate và chưa có Job Application.
- Ghi `legacy_intent = cv` vào `audit_history`, sau đó đổi category của email đã migration thành `job_application`.
- Giữ nguyên email và Candidate đã có Candidate; không dựng ngược Job Application cho lịch sử đó.
- Làm migration idempotent bằng điều kiện `NOT EXISTS` theo source email/Gmail message.
- Loại `EmailIntent.CV` khỏi enum, prompt LLM và consumer enqueue còn lại.
- Đổi contract trạng thái historical import từ `cv_count` sang `job_application_count` ở backend và frontend.
- Bổ sung integration test chạy migration thật trên PostgreSQL, downgrade revision marker rồi upgrade lại để chứng minh không duplicate.
- Sửa migration `064` để không tạo cùng index hai lần qua cả `index=True` và `op.create_index`.

# The real problem

Vấn đề không chỉ là đổi tên một enum. Hệ thống đang ở giữa expand–contract: dữ liệu cũ vẫn mang routing value `cv`, trong khi domain mới coi CV chỉ là tài liệu/evidence và Job Application mới là intent tuyển dụng. Nếu xóa compatibility code trước khi backfill, công việc HR chưa được giải quyết sẽ biến mất. Nếu backfill mọi email lịch sử, hệ thống lại bịa ra Job Application cho Candidate đã tồn tại.

# Why this solution

Migration chọn đúng ranh giới domain: chỉ email `cv` chưa sinh Candidate và chưa có Job Application mới cần được bảo toàn dưới dạng Job Application. Một SQL statement vừa insert vừa update category giúp thao tác nguyên tử. Audit history giữ giá trị cũ để giải thích quyết định migration, còn active contract chỉ còn `job_application`.

Điều kiện chống duplicate nằm trong chính truy vấn migration, nên chạy lại revision không phụ thuộc vào trạng thái tạm trong application process. Candidate chỉ được dùng làm điều kiện loại trừ và không bị update.

# Production shape

Khi deploy:

1. Alembic chạy revision `065` sau `064`.
2. PostgreSQL chọn email có `category = 'cv'`, loại email đã có Candidate hoặc Job Application.
3. Mỗi email hợp lệ tạo một Job Application với source/message reference và audit legacy.
4. Cùng statement đổi category email đó thành `job_application`.
5. Code mới chỉ phát và nhận routing intent `job_application`; historical import trả `job_application_count`.

# Other possible approaches

1. Viết management command Python đọc từng email rồi gọi `JobApplicationService`.
2. Backfill Job Application cho toàn bộ email `cv`, kể cả email đã tạo Candidate, rồi nối Candidate vào record mới.
3. Giữ `cv` trong enum vô thời hạn và normalize sang `job_application` ở mỗi consumer.

# Why I did not choose those alternatives

- Management command Python phù hợp khi migration cần gọi dịch vụ ngoài hoặc logic phải quan sát/chạy thủ công. Ở đây dữ liệu và invariant đều nằm trong PostgreSQL; command riêng tăng thêm deployment step và dễ bị bỏ sót.
- Backfill toàn bộ lịch sử phù hợp khi có source-of-truth đủ mạnh để tái tạo chính xác quan hệ. Spec nói rõ không được dựng ngược lịch sử Candidate vì dữ liệu cũ không đảm bảo một Job Application đáng tin cậy.
- Normalize mãi ở consumer phù hợp cho giai đoạn expand có nhiều phiên bản producer cùng chạy. Contract phase đã đến lúc đóng seam cũ; giữ compatibility làm taxonomy tiếp tục mơ hồ và cho phép producer mới vô tình phát `cv`.

# Key concepts to learn

- **Expand–contract migration**: thêm contract mới, migration dữ liệu cần giữ, chuyển consumer/producer, rồi xóa contract cũ.
- **Idempotent data migration**: kết quả lần chạy thứ hai giống lần đầu, thường nhờ unique invariant hoặc `NOT EXISTS`.
- **Domain boundary**: Job Application tồn tại trước Candidate; CV là tài liệu/evidence, không phải routing intent.
- **Audit preservation**: đổi trạng thái active nhưng giữ giá trị cũ dưới dạng lịch sử có cấu trúc.
- **Data-modifying CTE**: dùng `INSERT ... RETURNING` làm đầu vào cho `UPDATE` trong cùng statement nguyên tử.

# Common mistakes

- Chỉ đổi enum mà không migration dữ liệu cũ.
- Backfill mọi record có cùng nhãn mà không xét record đã được giải quyết.
- Dựa vào application-level “check rồi insert”, tạo race hoặc duplicate khi chạy lại.
- Xóa legacy value hoàn toàn, khiến auditor không biết record được tạo từ contract nào.
- Dùng `index=True` trong `sa.Column` đồng thời gọi `op.create_index` cùng tên trong migration Alembic.
- Đổi backend response field nhưng quên TypeScript client và UI consumer.

# Small example

Giả sử có ba email:

- A: `category=cv`, chưa có Candidate, chưa có Job Application → tạo Job Application, audit `legacy_intent=cv`, đổi category thành `job_application`.
- B: `category=cv`, Candidate có `source_email_message_id=B` → giữ nguyên, không tạo Job Application giả định.
- C: `category=cv`, đã có Job Application → bỏ qua để không duplicate.

Chạy migration lần nữa vẫn chỉ có Job Application của A và C.

# How to think about this next time

Khi loại một contract legacy, hãy lần lượt hỏi: dữ liệu nào còn là công việc chưa giải quyết, dữ liệu nào đã có domain outcome, invariant nào chứng minh idempotency, audit nào phải giữ, và producer/consumer/public field nào vẫn phát tán vocabulary cũ. Chỉ contract sau khi cả dữ liệu và mọi active edge đã chuyển xong.
