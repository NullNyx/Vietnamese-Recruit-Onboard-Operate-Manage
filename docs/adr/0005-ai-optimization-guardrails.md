# AI optimization guardrails

status: accepted

Vroom HR sẽ tối ưu AI Automation trước các Assistant, với Job Application recall ≥ 98% tổng thể và theo từng nhóm khó là hard guardrail; review rate, chi phí và latency chỉ được tối ưu sau khi giữ được recall. AI output chỉ là dữ liệu draft có provenance, còn Assistant luôn bị giới hạn bởi Read-Tool/Draft-Tool, không có đường ghi trực tiếp qua LLM. Rollout phải đi qua baseline, shadow, canary và rollback; provider fallback chỉ được dùng khi vẫn thỏa privacy và quality floor.

## Considered Options

- Tối ưu chatbot trước: bị loại vì không tác động trực tiếp đến Backbone Flow.
- Dùng confidence threshold tùy chỉnh theo từng Organization: bị loại vì khó kiểm soát, khó tái lập và có thể làm suy giảm recall.
- Cho LLM write trực tiếp khi confidence cao: bị loại vì phá vỡ human-in-the-loop và tăng rủi ro dữ liệu HR.

## Consequences

Có thể tăng số lượng item cần HR review và chi phí AI trong ngắn hạn. Đổi lại, hệ thống ưu tiên không bỏ sót Job Application, có thể đo lường theo evaluation set, và giữ ranh giới an toàn ở cấp cấu trúc thay vì chỉ dựa vào prompt.
