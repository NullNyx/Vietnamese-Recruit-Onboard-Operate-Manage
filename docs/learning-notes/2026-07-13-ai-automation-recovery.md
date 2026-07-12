# Task
Implement bounded retry và manual recovery cho AI Automation theo issue #175.

# What I changed
Lưu metadata lỗi/lần retry/thời điểm retry cho email và CV; khi provider lỗi, item được giữ lại với trạng thái an toàn và backoff hữu hạn. Thêm retry thủ công và phân loại email thủ công cho HR, đồng thời mở rộng review queue cho CV lỗi provider.

# The real problem
Provider failure trước đây bị coi như lỗi tạm thời của request, dễ làm mất ngữ cảnh hoặc khiến workflow dừng mà không có work item bền vững.

# Why this solution
Trạng thái và lịch retry nằm trong database, nên worker/API restart không làm mất pending item. Backoff cố định và giới hạn retry ngăn request storm; manual endpoint là đường thoát khi provider vẫn unavailable.

# Production shape
Sync lưu email trước; classification chỉ cập nhật trạng thái. CV đã lưu MinIO và CVDocument trước khi gọi provider. HR có thể retry hoặc hoàn tất thủ công từ review workflow.

# Other possible approaches
1. Dùng Redis-only queue; phù hợp cho workload ngắn hạn nhưng không phù hợp khi cần audit và không mất item sau restart.
2. Dùng workflow engine/queue chuyên dụng với delayed jobs; phù hợp khi volume lớn và cần scheduling phân tán.

# Why I did not choose those alternatives
Redis-only không đủ durable cho dữ liệu tuyển dụng. Workflow engine là speculative generality với deployment self-hosted hiện tại; database retry metadata và ARQ là seam nhỏ hơn.

# Key concepts to learn
Durable work item, bounded exponential backoff, idempotency bằng checksum, dead-letter/permanent failure, human-in-the-loop recovery.

# Common mistakes
Không fallback im lặng sang kết quả confidence thấp khi provider lỗi. Không retry vô hạn. Không xóa item pending khi tắt capability.

# Small example
Lần lỗi đầu đặt `ai_unavailable`, `retry_count=1`, `next_retry_at=now+60s`; provider hồi phục thì category được ghi và retry metadata được reset.

# How to think about this next time
Tách việc lưu event khỏi việc xử lý event. Mọi provider call phải có trạng thái durable, lịch retry hữu hạn và đường manual rõ ràng.
