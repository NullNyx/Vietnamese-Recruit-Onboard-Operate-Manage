# Task
Thiết lập telemetry có thể tái lập cho baseline AI Automation theo issue #200.

# What I changed
Mở rộng sự kiện rollout không chứa nội dung email để ghi prompt/policy version, retry failure, token usage và estimated cost; bổ sung migration và các metric tổng hợp tương ứng.

# The real problem
Telemetry cũ đo recall proxy và latency nhưng không đủ dữ liệu để giải thích một kết quả hoặc tính chi phí vận hành theo release.

# Why this solution
Metadata được ghi cùng event, còn report chỉ lấy event mới nhất theo email. Nhờ vậy metric không đếm nhiều lần retry như nhiều mẫu độc lập và không lưu raw content.

# Production shape
Migration 067 thêm các cột nullable-safe với default. Repository ghi event và tổng hợp retry failure, token và cost trong cùng operational window.

# Other possible approaches
1. Ghi telemetry vào hệ thống metrics bên ngoài (Prometheus/OpenTelemetry), phù hợp khi cần dashboard realtime và retention riêng.
2. Đọc log provider để dựng report hậu kỳ, phù hợp cho điều tra ad-hoc nhưng cần parsing log và dễ mất event.

# Why I did not choose those alternatives
Database event đã là seam durable hiện có và cần join với correction/inbox để tính recall proxy. External metrics không đủ business context; parsing log không bảo đảm đầy đủ hoặc tái lập.

# Key concepts to learn
Versioned telemetry, latest-event aggregation, cohort metrics, token accounting, retry failure và data minimization.

# Common mistakes
Không lưu raw prompt/email trong telemetry; không gộp provider error thành `other`; không cộng mọi retry như những email khác nhau.

# Small example
Hai event cùng Gmail message chỉ tính event mới nhất, nhưng event đó vẫn ghi `prompt_tokens`, `completion_tokens`, cost và `retry_failure`.

# How to think about this next time
Bắt đầu từ metric release cần quyết định, truy ngược metadata tối thiểu cần ghi, rồi thiết kế event không chứa dữ liệu nhạy cảm trước khi chọn dashboard.
