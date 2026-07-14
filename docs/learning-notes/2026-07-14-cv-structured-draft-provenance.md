# Task
Triển khai CV structured draft và Field Provenance cho issue #203.

# What I changed
- Bổ sung `FieldProvenance` và `CVFieldValidation` vào contract `ParsedCV`.
- Thêm kiểm tra deterministic: field thiếu, giá trị không xuất hiện trong source, email/phone mâu thuẫn và critical-field hallucination.
- Lưu provenance, validation findings và danh sách field HR đã xác nhận trên `CVDocument`.
- Khi parse lại, giữ nguyên field đã HR xác nhận.
- AI Automation chỉ cập nhật draft; không tự tạo Candidate.
- Thêm migration và mở rộng CV review response.

# The real problem
Confidence score tổng hợp không chứng minh một field là đúng. Một CV có thể có score cao nhưng email bị bịa hoặc bị lấy nhầm từ phần khác. Ngoài ra, tạo Candidate trong parser đã biến output AI thành write nghiệp vụ.

# Why this solution
Provenance được tạo ở application boundary bằng cách đối chiếu literal với OCR source, vì đây là bằng chứng có thể kiểm tra và không phụ thuộc lời giải thích của LLM. Các lỗi critical chặn trạng thái completed. Candidate promotion vẫn là action HR riêng.

# Production shape
Attachment metadata và validation diễn ra trước khi CV đi vào pipeline; nội dung đã OCR được dùng làm source evidence. `CVDocument` giữ draft JSON, provenance, validation errors và HR confirmations. Retry parse merge các field confirmed trước khi đánh giá lại field còn lại.

# Other possible approaches
1. Cho LLM trả luôn source span/token offset. Phù hợp khi OCR có offset ổn định và provider hỗ trợ structured output nghiêm ngặt.
2. Dùng search index hoặc embedding để tìm evidence gần nghĩa. Phù hợp với CV nhiều lỗi OCR hoặc paraphrase, nhưng cần calibration và vẫn phải có rule riêng cho critical fields.
3. Đưa toàn bộ validation vào database constraint. Phù hợp với invariant đơn giản, không phù hợp với đối chiếu văn bản và provenance.

# Why I did not choose those alternatives
Offset từ LLM không đáng tin cậy giữa các provider và dễ lệch sau redaction. Embedding có thể tìm nhầm evidence và không cho zero-tolerance hallucination. Database không nên biết semantics của CV; application service là seam đúng cho policy này.

# Key concepts to learn
- Field Provenance là evidence của từng field, không phải chain-of-thought.
- Draft khác write: AI có thể đề xuất dữ liệu nhưng không được tạo Candidate.
- Critical-field validation cần policy fail-closed.
- Human confirmation phải là state bền vững và được merge khi retry.

# Common mistakes
- Dùng confidence tổng thể để coi mọi field là đúng.
- Ghi Candidate ngay sau khi parse thành công.
- Để retry ghi đè dữ liệu HR đã xác nhận.
- Lưu prompt/raw CV vào audit log thay vì provenance tối thiểu.

# Small example
Nếu parser trả `email = a@example.com` nhưng source chỉ có `b@example.com`, draft nhận `critical_field_hallucination` và `conflicting_email`; CV vào review queue, không được tự hoàn tất hoặc tạo Candidate.

# How to think about this next time
Trước tiên hãy tách ba câu hỏi: AI đề xuất gì, source chứng minh gì, và HR đã xác nhận gì. Chỉ khi cả policy validation và human boundary đều đúng mới cho phép bước workflow tiếp theo.
