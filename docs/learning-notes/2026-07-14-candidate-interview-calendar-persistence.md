# Task
Khôi phục persistence tương thích cho các trường interview của Candidate và làm cho luồng schedule/reschedule/cancel hoạt động nhất quán với lớp Google Calendar.

# What I changed
- Bổ sung `calendar_event_id`, `interview_start_at`, `interview_timezone` vào `Candidate`.
- Migration 054 vẫn kiểm tra dữ liệu mồ côi nhưng không xoá projection tương thích trên Candidate.
- Schedule ghi cả `Interview` chuẩn hoá và các trường Candidate, đồng thời trả về Candidate.
- Reschedule/cancel có fallback đọc event từ Candidate khi chưa có Interview row.
- Cập nhật test harness để mô phỏng đúng các field và rollback.

# The real problem
Schema và service đã chuyển sang `Interview`, nhưng API/test contract vẫn đọc các reference trực tiếp từ Candidate. Vì vậy object có thể schedule thành công nhưng response thiếu event id, hoặc reschedule không tìm thấy event.

# Why this solution
Giữ `Interview` làm mô hình chuẩn cho dữ liệu mới, đồng thời duy trì Candidate như compatibility projection. Như vậy migration cũ, API hiện tại và các deployment đang nâng cấp dở đều không bị gãy.

# Production shape
Calendar create xảy ra trước commit. Sau thành công, Candidate và Interview cùng mang reference/timezone; reschedule patch đúng event cũ; terminal transition vẫn commit dù huỷ Calendar thất bại.

# Other possible approaches
1. Xoá hoàn toàn các field khỏi Candidate và sửa toàn bộ API/client/test để chỉ dùng Interview.
2. Chỉ giữ field trên Candidate và bỏ bảng Interview, đơn giản hoá persistence.

# Why I did not choose those alternatives
Phương án 1 là breaking change và không phù hợp với dữ liệu/deployment đang tồn tại. Phương án 2 làm mất mô hình chuẩn hoá cho participant, conflict và calendar sync; chỉ phù hợp với hệ thống rất nhỏ chưa có Interview domain.

# Key concepts to learn
- Compatibility projection và schema migration nhiều giai đoạn.
- Atomic side effect: external Calendar call trước database commit.
- Idempotent reschedule: patch event cũ, không tạo event mới.
- Best-effort side effect sau terminal transition.

# Common mistakes
- Chỉ thêm field vào SQLModel nhưng quên migration.
- Tạo Interview thành công nhưng không return/persist Candidate projection.
- Reschedule luôn giả định Interview row tồn tại.
- Để audit hoặc cancellation failure rollback hành động chính.

# Small example
```python
candidate.calendar_event_id = event.event_id
candidate.interview_start_at = start_resolved
candidate.interview_timezone = timezone
await candidate_repo.update(candidate)
```

# How to think about this next time
Trước khi sửa service, lập bảng contract: field nằm ở đâu, migration head tạo gì, response đọc từ đâu, và rollback cần phục hồi gì. Khi chuyển mô hình, hãy giữ một compatibility seam rõ ràng thay vì xoá ngay dữ liệu cũ.
