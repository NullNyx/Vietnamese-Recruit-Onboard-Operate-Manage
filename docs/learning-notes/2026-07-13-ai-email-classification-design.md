# Task

Thiết kế cải thiện tính năng AI phân loại email cho HR theo hướng giảm Job Application bị bỏ sót.

# What I changed

Chuẩn hóa thuật ngữ Job Application và Recruitment Inbox trong `CONTEXT.md`, ghi ADR về boundary giữa Job Application và Candidate, đồng thời lập kế hoạch triển khai classifier, evaluation, migration và rollout.

# The real problem

Vấn đề không chỉ là prompt phân loại `cv`. Intent `cv` đồng nhất nhầm ba việc khác nhau: nhận ra ý định ứng tuyển, tìm tài liệu CV và đưa một người vào Candidate pipeline. Vì vậy email ứng tuyển không có attachment dễ bị bỏ sót, còn email mơ hồ có thể tạo Candidate rác.

# Why this solution

Job Application trở thành vùng đệm domain trước Candidate. AI được phép ghi nhận đầu vào có khả năng ứng tuyển, nhưng trường hợp không chắc chắn phải hiện trong Recruitment Inbox và chỉ HR được promote thành Candidate. Thiết kế ưu tiên recall trong khi giữ boundary human-in-the-loop ở quyết định nghiệp vụ quan trọng.

# Production shape

Production dùng pipeline nhiều tầng: deterministic evidence, LLM structured output, calibrated policy và HR review band. Dữ liệu được đọc tăng dần theo nhu cầu; correction được dùng cho evaluation thay vì online learning. Phiên bản mới chạy shadow, sau đó canary và mới full rollout. Legacy `cv` chỉ được migration khi chưa tạo Candidate.

# Other possible approaches

1. Giữ intent `cv`, cải thiện prompt và tự tạo Candidate khi parse được attachment. Cách này phù hợp với hệ thống nhỏ nơi mọi application bắt buộc có CV chuẩn và inbox đầu vào đã được kiểm soát chặt.
2. Đưa mọi email nghi ngờ cho HR, không tự tạo Job Application. Cách này phù hợp khi lưu lượng rất thấp hoặc yêu cầu compliance cấm AI tạo bất kỳ record nghiệp vụ nào.
3. Dùng online learning/fine-tuning từ mọi correction. Cách này có thể phù hợp khi có dataset lớn, quy trình kiểm duyệt nhãn nghiêm ngặt và hạ tầng ML governance trưởng thành.

# Why I did not choose those alternatives

Giữ `cv` không giải quyết ứng tuyển thiếu attachment và tiếp tục trộn ingestion với Candidate admission. Review hoàn toàn thủ công không đạt mục tiêu giảm bỏ sót mà vẫn tiết kiệm công sức HR. Online learning trực tiếp khó kiểm soát correction sai, drift và dữ liệu cá nhân; repo hiện phù hợp hơn với evaluation có version và thay đổi model/prompt có kiểm soát.

# Key concepts to learn

- Recall quan trọng hơn accuracy tổng thể khi false negative có chi phí cao.
- Confidence của LLM chỉ hữu ích sau calibration.
- Domain boundary có thể ngăn output AI không chắc chắn làm ô nhiễm dữ liệu cốt lõi.
- Routing intent nên là một quyết định workflow; source và đặc điểm phụ là thuộc tính khác.
- Shadow và canary giảm rủi ro khi thay classifier production.

# Common mistakes

- Coi file tên `CV.pdf` là bằng chứng chắc chắn của Job Application.
- Dùng sender làm danh tính Candidate trong email referral/agency.
- Tự gộp các email chỉ vì cùng địa chỉ gửi.
- Lưu chain-of-thought hoặc toàn bộ email vô thời hạn để “debug AI”.
- Đổi provider error thành `other`, khiến email biến mất khỏi review.
- Đo accuracy trên dataset mất cân bằng thay vì recall theo nhóm khó.

# Small example

Agency gửi một email chứa ba CV. Email có routing intent `job_application`, source `agency`, và tạo ba Job Application cùng tham chiếu email nguồn. Nếu AI chỉ nhận ra hai người, item vẫn vào Recruitment Inbox để HR xác nhận việc tách; chưa Job Application nào tự trở thành Candidate.

# How to think about this next time

Bắt đầu từ chi phí của từng loại sai, sau đó xác định record nào AI được phép tạo và quyết định nào bắt buộc có con người. Chỉ khi domain boundary rõ mới chọn model, prompt, threshold và UI. Luôn thiết kế evaluation, audit, migration và rollback cùng lúc với happy path.
