# Task

Hoàn thiện action để HR sửa `source` của Job Application cho issue #202, đồng thời mở rộng integration journey cho email không chắc chắn vào Recruitment Inbox.

# What I changed

- Thêm `POST /api/recruitment/job-applications/{id}/source` chỉ dành cho HR.
- `JobApplicationDecisionService.correct_source()` khoá bản ghi, chặn Job Application đã dismissed, cập nhật source và ghi audit history.
- Bổ sung test service/API cho quyền HR và audit trail.
- Bổ sung integration test database: email ứng tuyển không có CV, confidence thấp, được route idempotent vào Recruitment Inbox, không tạo Job Application và vẫn có Gmail audit trail.

# The real problem

AI có thể suy luận sai nguồn (direct, referral, agency), nhưng source là metadata nghiệp vụ mà HR cần sửa sau review. Nếu chỉ cho chọn source lúc split, Job Application đã tạo tự động không có action sửa rõ ràng.

# Why this solution

Action đặt ở Job Application decision service, tách khỏi ingestion service. Vì vậy AI Automation vẫn không nhận interface để thực hiện HR decision, còn mọi thay đổi source đều có audit trail và principal HR.

# Production shape

Router xác thực HR, gọi application service. Service đọc bản ghi `FOR UPDATE`, từ chối bản ghi dismissed, append audit history, cập nhật repository và commit trong cùng transaction. API trả về source và status mới nhất.

# Other possible approaches

1. Sửa source trực tiếp trong inbox action. Phù hợp khi Job Application chưa tồn tại và HR đang split một email nhiều ứng viên.
2. Thêm generic `PATCH /job-applications/{id}` cho mọi field. Phù hợp nếu có nhiều field HR được phép sửa và có policy validation riêng cho từng field.

# Why I did not choose those alternatives

1. Inbox không bao phủ Job Application đã được tạo tự động từ confident classification.
2. Generic patch làm mờ các action nghiệp vụ, dễ cho phép thay đổi lifecycle/candidate linkage vô tình và làm audit khó diễn giải.

# Key concepts to learn

- Job Application khác Candidate: HR mới promote Job Application thành Candidate.
- `source` là provenance nghiệp vụ, không phải lifecycle state.
- Idempotency giữ retry email không tạo duplicate work item.
- Audit trail phải chứa giá trị trước, giá trị sau, người thực hiện và thời điểm.

# Common mistakes

- Cho AI ingestion service gọi HR decision service.
- Hard-delete hoặc mở lại item dismissed khi retry.
- Sửa source mà không lưu previous value.
- Dùng email có CV làm điều kiện bắt buộc cho `job_application`.

# Small example

HR phát hiện email bị gán `direct` nhưng thực chất là agency:

```http
POST /api/recruitment/job-applications/{id}/source
{"source":"agency"}
```

Job Application vẫn ở status `new`, nhưng audit history có `source_corrected` với `previous_source: direct`.

# How to think about this next time

Xác định action thuộc boundary nào trước: ingestion chỉ tạo draft/domain input; HR decision mới thay đổi dữ liệu đã được review. Sau đó kiểm tra action có authz, transaction, auditability và integration proof cho retry/idempotency hay chưa.
