# Requirement / BA Doc — Vroom HR

## 1. Mục tiêu

Vroom HR là một HR Workflow Assistant cho doanh nghiệp Việt Nam, không phải một HRM suite đầy đủ. Mục tiêu là giảm thao tác lặp cho HR ở các tác vụ hằng ngày, giữ trạng thái rõ ràng, và vẫn đảm bảo human-in-the-loop với các hành động có tác động nghiệp vụ.

## 2. Phạm vi

### 2.1 In scope

- Tiếp nhận và phân loại email đầu vào
- CV parsing từ file đính kèm
- Tạo và theo dõi Candidate pipeline
- HR review, schedule interview, accept/reject/archive Candidate
- Gửi email phản hồi / lời mời / congratulations email
- Onboarding checklist cho Candidate đã accepted
- Audit trail cho các hành động quan trọng
- AI Assistant HR-only: đọc, tóm tắt, draft, gợi ý, không tự write

### 2.2 Out of scope

- Payroll engine đầy đủ
- Attendance system đầy đủ
- Employee-facing features (self-service, portal, assistant)
- HR policy engine đầy đủ
- Plugin/app store
- Thay thế HRM hiện có của doanh nghiệp

## 3. Stakeholders

- HR: người dùng duy nhất, xử lý inbox, CV, lịch phỏng vấn, onboarding
- Candidate (gián tiếp): nhận email phản hồi, lịch phỏng vấn từ hệ thống

## 4. Business goals

- Giảm thời gian lọc email và CV
- Giảm sai sót khi theo dõi trạng thái ứng viên / onboarding
- Giảm vòng trao đổi thủ công trong xếp lịch phỏng vấn
- Giữ traceability và audit-by-design
- Dùng AI đúng vai: đọc, tóm tắt, gợi ý, draft; không tự write

## 5. Core workflows

### 5.1 Email → triage → CV parse → Candidate

1. Email đi vào inbox trung tâm.
2. Hệ thống phân loại email theo ngữ cảnh.
3. Nếu có CV đính kèm, hệ thống parse và tóm tắt.
4. Hệ thống tạo hoặc cập nhật Candidate.
5. HR review kết quả, chỉnh sửa nếu cần, rồi chốt hành động.
6. Mọi hành động quan trọng được log audit.

### 5.2 Candidate accepted → onboarding hoàn tất

1. HR chốt Candidate sang accepted.
2. Hệ thống tạo onboarding flow tương ứng.
3. Checklist onboarding được sinh từ template phù hợp.
4. HR hoàn tất từng task.
5. Khi HR xác nhận case hoàn tất, Candidate trạng thái chốt.
6. Trạng thái và lịch sử thay đổi được lưu audit.

### 5.3 AI Assistant draft flow (HR-only)

1. HR mở assistant surface trong onboarding case.
2. Assistant đọc dữ liệu case, candidate, checklist.
3. Assistant có thể draft email, contract, reminder.
4. HR review form / preview đã điền sẵn.
5. Chỉ sau xác nhận của HR thì UI mới write thật.

## 6. Pain points

- Email đầu vào lẫn lộn, khó phân loại
- CV nhiều format, đọc thủ công
- Xếp lịch phỏng vấn nhiều vòng
- Onboarding checklist thiếu chuẩn hóa
- Không có dashboard trạng thái tổng quan
- Thiếu audit trail và traceability

## 7. Business rules

- Candidate là người đang trong pipeline tuyển dụng.
- Candidate accepted mới mở onboarding.
- AI không được tự ý gửi email hay ghi đè dữ liệu nguồn.
- Human-in-the-loop là bắt buộc cho hành động có write effect.

## 8. User needs

### 8.1 HR

- Xem nhanh trạng thái email và Candidate
- Có tóm tắt CV để ra quyết định nhanh hơn
- Tạo nháp thư mời / phản hồi
- Thấy onboarding còn thiếu gì
- Truy vết ai làm gì, lúc nào

## 9. Edge cases

- Email không có CV đính kèm
- CV parse lỗi hoặc confidence thấp
- Candidate đổi lịch phỏng vấn nhiều lần
- Candidate accepted nhưng onboarding dang dở
- Dữ liệu thiếu hoặc mơ hồ → fallback thủ công

## 10. Acceptance criteria

- HR có thể đi từ email đầu vào đến Candidate tạo mới / cập nhật
- HR có thể accept Candidate và mở onboarding
- Onboarding hoàn tất khi HR chốt case
- Assistant chỉ draft, không tự write
- Audit log ghi được actor, action, object, timestamp
- Tất cả trạng thái chính có thể xem rõ trên UI / dashboard

## 11. Source references

- `CONTEXT.md`
- `docs/decisions/0002-scope-recruit-to-onboard-backbone-plus-assistant.md`
- `docs/decisions/0014-workflow-agnostic-hr-assistant.md`
- `docs/decisions/0015-onboarding-hr-only-no-employee.md`
- `docs/decisions/0006-assistant-read-tools-and-draft-tools.md`
- `docs/bao-cao-do-an-tot-nghiep-vroom-hr.md`
