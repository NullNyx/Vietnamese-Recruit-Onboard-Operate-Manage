# Kế hoạch cải thiện AI phân loại email tuyển dụng

## Mục tiêu

Giảm Job Application bị bỏ sót mà không cho AI tự đưa dữ liệu không chắc chắn vào Candidate pipeline.

Tiêu chí phát hành ban đầu:

- Job Application recall ≥ 98% trên evaluation set.
- Tỷ lệ email vào `needs_classification` ≤ 15%.
- Không giảm recall so với classifier production hiện tại.
- Báo cáo riêng nhóm email ứng tuyển không có CV đính kèm.

## Phạm vi

Bao gồm:

- Intent `job_application` thay cho `cv`.
- Job Application tồn tại trước Candidate.
- Recruitment Inbox thống nhất cho review và correction.
- Classifier nhiều tầng và policy ưu tiên không bỏ sót.
- Evaluation feedback, shadow run, canary và migration giới hạn.

Không bao gồm:

- Tự động gửi email xin bổ sung CV.
- Online learning từ correction của HR.
- Tạo ngược Job Application cho Candidate hiện có.
- Cho HR chỉnh raw confidence threshold.

## Luồng quyết định

1. Gmail ingestion lưu metadata tối thiểu và trạng thái xử lý idempotent.
2. Deterministic rules trích xuất evidence nhưng không tự quyết định intent.
3. Classifier nhận dữ liệu theo mức cần thiết:
   - sender, subject, body và attachment metadata trước;
   - thread context khi cần liên kết email bổ sung;
   - nội dung attachment khi cần xác định hồ sơ hoặc số người ứng tuyển.
4. Classifier trả structured output: routing intent, confidence, evidence kiểm chứng được và source hints. Không lưu hoặc hiển thị chain-of-thought.
5. Calibrated policy xử lý kết quả:
   - đủ chắc chắn là `job_application` → tự tạo Job Application;
   - không chắc chắn → `needs_classification` trong Recruitment Inbox;
   - provider lỗi → retry/backoff rồi manual review, không đổi thành `other`.
6. HR có thể sửa intent, liên kết/tách application, gán Job Opening, dismiss hoặc promote Job Application thành Candidate.

## Quy tắc domain

- Job Application đại diện cho một người ứng tuyển vào tối đa một Job Opening.
- Một email agency chứa nhiều hồ sơ tạo nhiều Job Application dùng chung email nguồn.
- Cùng Gmail thread mặc định thuộc cùng Job Application.
- Ngoài thread, hệ thống chỉ đề xuất liên kết; HR xác nhận.
- Sender và người ứng tuyển là hai danh tính khác nhau.
- Khi email có nhiều đặc điểm, `job_application` là routing intent ưu tiên; `direct`, `employee_referral`, `agency` là source.
- HR bác bỏ application bằng trạng thái `dismissed`, không hard-delete.

## Recruitment Inbox

Một inbox chung, có filter tối thiểu:

- `needs_classification`
- `needs_information`
- `ready_for_review`
- `resolved`

Mỗi item hiển thị prediction, confidence đã hiệu chỉnh, evidence chính, nguồn, attachment metadata và lịch sử correction. Các action phải giữ audit trail và chống xử lý lặp.

## Evaluation và dữ liệu

Mặc định chỉ lưu prediction, correction, model/prompt version, policy version, metadata tối thiểu và timestamp. Nội dung email dùng để phân loại là dữ liệu tạm.

HR có thể chủ động chọn từng mẫu cho evaluation set. Trước khi lưu, mẫu phải được redaction dữ liệu nhạy cảm. Correction là nhãn đánh giá; không tự động sửa prompt, fine-tune model hoặc ảnh hưởng trực tiếp email tiếp theo.

Evaluation set phải có các nhóm khó:

- ứng tuyển không có CV;
- CV do nhân viên chuyển tiếp;
- agency gửi một hoặc nhiều ứng viên;
- email vừa giới thiệu dịch vụ vừa gửi hồ sơ;
- email bổ sung hoặc sửa CV;
- cùng sender ứng tuyển nhiều vị trí;
- attachment có tên giống CV nhưng không phải ứng tuyển;
- tiếng Việt, tiếng Anh và nội dung trộn ngôn ngữ.

## Các giai đoạn triển khai

### 1. Baseline

- Đóng băng evaluation set đã redaction.
- Đo classifier hiện tại theo recall, precision, review rate và từng nhóm khó.
- Ghi nhận model, prompt và dataset version để kết quả tái lập được.

### 2. Domain và persistence

- Thêm Job Application cùng source email/thread references, source, Job Opening tùy chọn và lifecycle.
- Bảo đảm uniqueness/idempotency khi worker retry.
- Tách Candidate promotion thành action do HR thực hiện.

### 3. Classifier và policy

- Đổi output contract từ `cv` sang `job_application`.
- Thêm deterministic evidence extraction và progressive data loading.
- Hiệu chỉnh confidence; ánh xạ policy cấp Organization thay vì expose raw threshold.
- Bảo vệ prompt injection: email và attachment luôn là untrusted data; classifier không có tool/write capability.

### 4. Recruitment Inbox

- Xây queue/filter và chi tiết evidence.
- Thêm correction, split/link, dismiss, gán Job Opening và promote Candidate.
- Thêm audit log và metrics cho false negative/false positive.

### 5. Migration

- Với legacy `cv` chưa tạo Candidate, tạo Job Application idempotently.
- Giữ nguyên Candidate hiện có.
- Giữ legacy intent trong audit; không backfill toàn bộ email lịch sử.

### 6. Rollout

- Shadow classifier mới trên production traffic, không ảnh hưởng workflow.
- So sánh theo acceptance criteria và nhóm khó.
- Canary bằng phân vùng email ổn định; theo dõi recall proxy, correction rate, review rate, latency, provider errors và duplicate creation.
- Rollback về classifier/policy cũ khi vi phạm guardrail.
- Full rollout chỉ sau khi canary đạt tiêu chí.

## Kiểm thử bắt buộc

- Unit test cho evidence rules, structured output validation và policy boundary.
- Integration test từ Gmail message đến Job Application/Recruitment Inbox.
- Idempotency test cho retry, thread linking và migration.
- Permission test bảo đảm AI không thể promote Candidate.
- Privacy test bảo đảm raw content không được lưu mặc định.
- Regression evaluation theo model/prompt/policy version.

## Điều kiện hoàn tất

- Các metric phát hành đạt ngưỡng trên evaluation set và shadow/canary.
- HR xử lý được toàn bộ trường hợp không chắc chắn trong Recruitment Inbox.
- Không có đường AI nào tự tạo Candidate.
- Migration có thể chạy lại an toàn và không thay đổi Candidate hiện hữu.
- Có dashboard/telemetry đủ phát hiện missed application proxy, correction spike, retry failure và duplicate application.
