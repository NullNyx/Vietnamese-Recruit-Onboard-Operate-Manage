# Task

Hoàn thiện issue #205 cho shadow/canary rollout của classifier Job Application: biến operational telemetry thành dashboard contract và chặn full rollout khi vận hành không an toàn.

# What I changed

- Bổ sung `retry_failure_rate`, token usage và estimated cost vào response telemetry của Admin API.
- Bổ sung các operational release gates cho p95 latency, provider error rate và retry failure rate.
- Bổ sung endpoint guardrail để tự động rollback rollout đang active khi operational guardrail vượt ngưỡng.
- Thêm test chứng minh candidate có recall tốt vẫn bị chặn nếu operational guardrail vượt ngưỡng và shadow không tạo duplicate workflow.

# The real problem

Recall là hard guardrail quan trọng nhưng chưa đủ. Candidate có thể phân loại đúng mà làm provider chậm, lỗi hoặc retry thất bại nhiều, khiến worker và workflow production không ổn định.

# Why this solution

Threshold vận hành được giữ trong module rollout, không cho Organization tự nhập. Release gate trả về failure codes có cấu trúc nên API và operator có thể dừng rollout hoặc rollback cùng một contract.

# Production shape

Telemetry được tổng hợp theo email mới nhất, hiển thị chất lượng workflow cùng latency, provider error, retry failure và chi phí. Full rollout chỉ được cấu hình khi mọi hard và operational gate đều đạt; nếu rollout active vi phạm gate, endpoint guardrail tự động chuyển về stable. Stable version vẫn được giữ để rollback.

# Other possible approaches

1. Cho HR tự cấu hình latency/error threshold.
2. Chỉ cảnh báo trên dashboard nhưng vẫn cho phép full rollout.
3. Dùng circuit breaker runtime để tự chuyển traffic mà không qua release gate.

# Why I did not choose those alternatives

- Threshold tùy chỉnh làm policy mất tính tái lập và có thể vô hiệu hóa guardrail; chỉ phù hợp khi có governance và đánh giá riêng.
- Cảnh báo không chặn được rollout nguy hiểm; phù hợp cho metric tối ưu thứ cấp, không phù hợp hard guardrail.
- Circuit breaker hữu ích để giảm blast radius tức thời nhưng không thay thế release decision/audit và không giải quyết việc so sánh candidate.

# Key concepts to learn

- Hard guardrail và operational guardrail.
- Release gate machine-readable.
- Stable retained state để rollback.
- Telemetry contract giữa persistence, service và dashboard.

# Common mistakes

- Chỉ đo recall rồi bỏ qua provider error và retry failure.
- Expose raw threshold cho UI.
- Ghi telemetry nhưng không đưa metric vào response operator sử dụng.

# Small example

Một candidate đạt recall 99% nhưng p95 latency 2.1 giây và retry failure 5.1% sẽ nhận các failure code tương ứng và không thể promote lên full.

# How to think about this next time

Bắt đầu từ câu hỏi “điều gì có thể làm production unsafe dù output đúng?”. Mỗi failure mode cần một metric, một threshold được sở hữu bởi policy, một failure code và một test transition.
