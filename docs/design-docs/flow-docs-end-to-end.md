# Flow Docs Chi Tiết End-to-End — Vroom HR

Mục tiêu: chốt luồng nghiệp vụ onboarding cho Vroom HR, tập trung hỗ trợ HR giảm thao tác thủ công. HR là actor duy nhất. Hệ thống không chuẩn hóa hay áp đặt workflow của doanh nghiệp.

## 1. Design principle

### Workflow agnostic

Vroom HR không áp đặt quy trình onboarding chuẩn cho mọi doanh nghiệp.

Hệ thống chỉ cung cấp công cụ để HR:

- theo dõi
- nhắc việc
- tổng hợp
- soạn thảo
- quản lý checklist
- quản lý tài liệu

Mọi quyết định nghiệp vụ vẫn thuộc về doanh nghiệp và HR.

### Tiêu chí giữ / bỏ tính năng

Hỏi:

> Tính năng này có giúp HR giảm thao tác thủ công không?

Nếu có → giữ.
Nếu tính năng:

- quyết định thay doanh nghiệp
- áp đặt workflow
- mô hình hóa quá sâu quy trình nội bộ
- phụ thuộc cứng vào chính sách từng công ty

→ bỏ hoặc giảm phạm vi.

### AI responsibility

AI MAY:

- ✓ Draft
- ✓ Summarize
- ✓ Suggest
- ✓ Extract
- ✓ Remind

AI MUST NOT:

- ✗ Approve
- ✗ Reject
- ✗ Confirm onboarding completion
- ✗ Decide business workflow
- ✗ Replace HR decisions

### Design constraints

- Workflow agnostic — không áp đặt quy trình
- Human confirmation required before write action
- AI only suggests, never auto-confirms
- All AI-generated content editable by HR
- Every write action audited
- System supports configurable templates

## 2. Phạm vi

### 2.1 In scope

- Onboarding sau Candidate Accepted — hỗ trợ HR theo dõi và điều phối các hoạt động onboarding
- Document tracking
- Contract drafting
- Onboarding checklist
- Timeline + reminder
- Views cho dashboard / detail / task board
- AI hỗ trợ draft, summarize, checklist suggestion, information extraction

### 2.2 Out of scope

- Employee lifecycle (HRM)
- Employee portal / self-service
- Digital signature execution
- Payroll / attendance
- Asset management thực thi
- IT/Admin provisioning thực thi
- Workflow engine cho Manager / IT / Admin
- Performance review workflow chuẩn hóa
- Quản lý nhân sự sau onboarding

## 3. Domain model

### 3.1 Candidate

Record trong pipeline tuyển dụng, theo dõi bởi HR.

### 3.2 Onboarding Case

Onboarding Case là thực thể trung tâm. Mỗi Candidate Accepted tạo một Onboarding Case. Mọi dữ liệu onboarding gắn vào case này.

State machine:

```
In Progress
   ├────► Completed
   └────► Cancelled
```

- In Progress: đang xử lý onboarding
- Completed: HR xác nhận case đã xong theo tiêu chí của doanh nghiệp
- Cancelled: ứng viên không đi làm / rút offer / công ty hủy

```
Candidate Accepted
        │
        ▼
Create Onboarding Case (In Progress)
        │
        ├── (HR xác nhận hoàn tất) ──► Completed
        └── (Hủy) ──► Cancelled
```

### 3.3 Business rule: onboarding complete

Không hard-code rule toàn cục cho mọi công ty.

Onboarding Complete là do HR xác nhận case đã xong theo checklist và quyết định nội bộ của doanh nghiệp.

Hệ thống chỉ hỗ trợ:

- hiển thị trạng thái pending
- tổng hợp mục còn thiếu
- nhắc việc theo deadline

### 3.4 Review / probation / performance

Không mô hình hóa thành business module riêng.

Nếu cần nhắc các mốc (ngày bắt đầu, ngày hết thử việc, ngày review) thì chỉ coi đó là deadline / reminder / task. Không xây workflow riêng.

## 4. Business modules

### 4.1 Document Management

Mục tiêu: giảm thời gian kiểm tra và nhắc hồ sơ.

**Tính năng:**

- checklist giấy tờ theo template
- DocumentItem tách rõ hai thuộc tính:
  - `required: true/false`
  - `status: missing / received / verified / rejected`
- template có thể thay đổi theo doanh nghiệp hoặc theo vị trí
- AI gợi ý danh sách theo ngữ cảnh
- AI phát hiện hồ sơ thiếu, nhắc HR
- AI extract thông tin từ giấy tờ (CCCD, CV) để điền field

**Flow:**

1. Onboarding case created → generate document checklist
2. HR review checklist, sửa nếu cần
3. HR theo dõi trạng thái từng giấy tờ
4. AI nhắc HR khi còn missing gần deadline
5. HR hoàn tất document step theo tiêu chí của doanh nghiệp

### 4.2 Contract Assistant

Mục tiêu: giảm thời gian soạn tài liệu. Không quản lý chữ ký.

**Nguyên tắc:** AI điền template, không sinh nội dung pháp lý từ đầu.

- AI nhận template của công ty
- AI điền thông tin candidate (tên, vị trí, lương, ngày bắt đầu, v.v.)
- AI highlight placeholder để HR review
- HR review, sửa, export ra ngoài để ký

**Tài liệu hỗ trợ:**

- Offer letter
- Labor contract (fill template)
- NDA
- Welcome email

**Contract status:**

- Draft
- Ready
- Sent
- Signed
- Cancelled

**Flow:**

1. Onboarding case created → generate contract draft từ template
2. HR review, sửa placeholder → mark Ready
3. HR tải xuống / copy bản final và gửi ra ngoài
4. HR update status: Sent → Signed sau khi có phản hồi

### 4.3 Task Management

Mục tiêu: HR nhìn một màn hình biết case đang kẹt ở đâu.

**Tính năng:**

- task list generated từ template
- mỗi task có: task category (HR / IT / Admin / Manager — do doanh nghiệp tự định nghĩa), owner, due date, status, note
- HR assign / update owner
- trạng thái: pending / in_progress / completed / blocked

**Flow:**

1. Onboarding case created → tasks tự sinh theo template
2. HR xem toàn bộ task, sửa owner / category nếu cần
3. HR update tiến độ khi task hoàn tất
4. HR dùng task board để theo dõi case còn thiếu gì

### 4.4 Timeline & Reminder

Mục tiêu: HR không phải tự nhớ.

**Tính năng:**

- timeline: Candidate Accepted → Documents → Contract → Tasks → Start Date
- deadline fromng item do HR hoặc template quyết định
- reminder tự động
- AI nhắc nội bộ theo deadline

**Flow:**

1. Hệ thống theo dõi deadline từ document checklist + task list + contract status
2. Đến mốc → AI gửi nhắc nội bộ
3. HR xem timeline và ưu tiên case cần xử lý

## 5. AI capabilities

AI là capability xuyên suốt, không phải module nghiệp vụ riêng.

### 5.1 Document checklist suggestion

- gợi ý checklist theo ngữ cảnh
- phát hiện hồ sơ thiếu
- sinh email yêu cầu bổ sung

### 5.2 Information extraction

- đọc CCCD, CV, giấy tờ
- tự động điền field
- detect thiếu thông tin

### 5.3 Template filling

- điền template offer / contract / NDA / welcome email
- highlight placeholder còn thiếu

### 5.4 Email drafting

- draft email nhắc hồ sơ
- draft email gửi lịch / nhắc ngày đi làm
- draft email follow-up theo ngữ cảnh

### 5.5 Activity summary

- daily / weekly / on-demand summary
- tổng hợp case pending / overdue
- tổng hợp hồ sơ chưa complete

## 6. Views

Views chỉ query dữ liệu từ business modules.

### 6.1 Onboarding Dashboard

Màn hình tổng quan case đang active.

Hiển thị:

- progress của từng case
- documents %
- tasks %
- contract status
- pending / overdue

### 6.2 Onboarding Case Detail

Màn hình chi tiết một Onboarding Case.

Hiển thị:

- candidate info
- document checklist
- contract draft/status
- task board
- timeline

### 6.3 Task Board

Màn hình xử lý task onboarding.

Hiển thị:

- task theo owner
- due date
- status
- pending items

### 6.4 Timeline View

Màn hình theo dõi mốc thời gian và reminder.

## 7. Audit & traceability

Mọi hành động có write effect ghi audit:

- actor (luôn là HR)
- action
- object (case ID, task ID, document ID)
- timestamp
- before/after nếu có
- source: Manual / AI Suggestion / System

## 8. Next step

Sau review và chốt flow này → data model draft chi tiết → UX / screen map.
