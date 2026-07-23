# Kịch bản Demo Hệ thống Vroom HR — Sidebar toàn tập

> **Phiên bản:** 1.0  
> **Mục đích:** Trình diễn toàn bộ tính năng hệ thống qua sidebar, dành cho HR Admin và Employee (ESS)  
> **Thời gian dự kiến:** 60–90 phút  
> **Người demo:** HR Admin (có thể là dev, PM, hoặc QA)

---

## Mục lục

- [Phần 1: Chuẩn bị & Seed Data](#phần-1-chuẩn-bị--seed-data)
- [Phần 2: HR Admin Demo — 16 Sidebar Mục](#phần-2-hr-admin-demo--16-sidebar-mục)
  - [#1: Dashboard & Metrics](#1-dashboard--metrics)
  - [#2: Recruitment Inbox](#2-recruitment-inbox)
  - [#3: Candidates](#3-candidates)
  - [#4: Job Openings](#4-job-openings)
  - [#5: Interview Schedule](#5-interview-schedule)
  - [#6: CV Review (Parse)](#6-cv-review-parse)
  - [#7: Recruitment Metrics](#7-recruitment-metrics)
  - [#8: Onboarding Processes](#8-onboarding-processes)
  - [#9: Employee List](#9-employee-list)
  - [#10: Employee Requests](#10-employee-requests)
  - [#11: Attendance & Allowlist](#11-attendance--allowlist)
  - [#12: Payslips](#12-payslips)
  - [#13: Knowledge Base](#13-knowledge-base)
  - [#14: Gmail Channel](#14-gmail-channel)
  - [#15: AI & System Settings](#15-ai--system-settings)
  - [#16: AI Assistant (HR)](#16-ai-assistant-hr)
- [Phần 3: Employee Self-Service (ESS) Demo](#phần-3-employee-self-service-ess-demo)
  - [#17: Employee Dashboard](#17-employee-dashboard)
  - [#18: Attendance (ESS)](#18-attendance-ess)
  - [#19: My Requests](#19-my-requests)
  - [#20: Payslips (ESS)](#20-payslips-ess)
  - [#21: AI Assistant (Employee)](#21-ai-assistant-employee)
- [Phần 4: Edge Cases](#phần-4-edge-cases)
  - [EC1: Employee không access admin page](#ec1-employee-không-access-admin-page)
  - [EC2: Không auth → redirect /login](#ec2-không-auth--redirect-login)
  - [EC3: Logout → redirect /login](#ec3-logout--redirect-login)
- [Phần 5: Phụ lục](#phần-5-phụ-lục)

---

## Phần 1: Chuẩn bị & Seed Data

### Yêu cầu hệ thống

| Thành phần | URL | Ghi chú |
|---|---|---|
| Frontend (Next.js) | http://localhost:3000 | Proxy sang backend :8000 |
| Backend (FastAPI) | http://localhost:8000 | Swagger: http://localhost:8000/docs |
| PostgreSQL | localhost:5432 | user/pass/db = postgres/postgres/vroom_hr |
| Docker services | `docker compose up -d` | Chạy tất cả services |

### Tài khoản mặc định

| Vai trò | Email | Mật khẩu | Ghi chú |
|---|---|---|---|
| **Admin chính** | `admin@vroomhr.com` | `VroomAdmin!2026` | Dùng để demo HR |
| **Admin (seed_all)** | `hr@vroom.com` | `admin123` | Tạo bởi seed_all.py |
| **Employee** | `employee.qa@vroom.example.com` | (cần tạo account) | Cần HR tạo account trước |

### Bước 1: Kiểm tra Docker services

```bash
docker compose ps
# Kỳ vọng: postgres, redis, minio, backend, frontend đều Running
```

### Bước 2: Chạy seed data toàn diện

Có **2 lựa chọn** seed data, tuỳ vào nhu cầu demo:

#### Lựa chọn A: Seed cơ bản (auto-seed, đã bật sẵn)

Nếu `AUTH_AUTO_SEED_SAMPLE_DATA=true` (mặc định), backend tự động seed khi khởi động:
- 2 Departments, 2 Positions
- 1 Employee (Hoang Xuan Nguyen)
- 4 Attendance Records
- 2 Payslips

> **Phù hợp:** Demo nhanh, kiểm tra CI, hoặc chạy E2E test.

#### Lựa chọn B: Seed toàn diện (khuyến nghị cho stakeholder demo)

Chạy script `seed_all.py` để tạo 100+ records dữ liệu Việt Nam hoá:

```bash
cd backend
uv run python scripts/seed_all.py
```

Script này tạo:

| Domain | Số lượng | Ghi chú |
|---|---|---|
| Departments | 6 | Ban Giám Đốc, Phòng Kỹ Thuật, Nhân Sự... |
| Positions | 24 | CEO, CTO, Senior Backend, Frontend... |
| **Employees** | **55** | 8 key roles + 47 regular, 3 inactive |
| **Job Openings** | **12** | 11 open, 1 closed |
| **Candidates** | **55** | new/reviewing/interview_scheduled/accepted/rejected/archived |
| **Interviews** | **50** | scheduled/completed/cancelled |
| **Attendance** | ~900 | 8 weeks x 5 days x active employees |
| **Payslips** | ~160 | 3 tháng gần nhất x active employees |
| **Onboarding** | **15** | Processes từ accepted candidates |
| **Employee Requests** | **60** | leave + overtime, mixed statuses |

> **Mật khẩu admin sau seed_all: `hr@vroom.com` / `admin123`**

#### Seed bổ sung (tuỳ chọn)

Sau `seed_all.py`, có thể chạy thêm:

```bash
# Seed emails vào Gmail Inbox (cần Google OAuth đã connect)
cd backend && uv run python -m scripts.seed_gmail --categories recruitment --count 5

# Seed dữ liệu chấm công 1 tháng
cd backend && uv run python -m scripts.seed_attendance

# Seed leave balances + leave requests
cd backend && uv run python -m scripts.seed_leave

# Seed payroll configs (salary, allowances, dependents)
cd backend && uv run python -m scripts.seed_payroll
```

### Bước 3: Tạo Employee Account cho demo ESS

Để demo Employee Self-Service, cần tạo tài khoản cho 1 employee:

**Cách 1: Qua UI (dễ nhất)**
1. Login `admin@vroomhr.com` / `VroomAdmin!2026`
2. Vào **Employees → Employee List**
3. Click vào employee bất kỳ (VD: "Hoang Xuan Nguyen" hoặc "Nguyễn Minh Tuấn")
4. Click **"Tạo tài khoản"** → ghi lại mật khẩu tạm thời

**Cách 2: Qua API (nhanh)**

```bash
# Tìm employee ID
curl -s http://localhost:8000/api/employees | jq '.items[0] | {id, full_name, email}'

# Tạo account (thay EMPLOYEE_ID bằng ID thật)
curl -s -X POST "http://localhost:8000/api/employees/${EMPLOYEE_ID}/account" \
  -H "Cookie: access_token=..." | jq
```

---

## Phần 2: HR Admin Demo — 16 Sidebar Mục

### #1: Dashboard & Metrics

**Mục tiêu:** Xem tổng quan hệ thống — recruitment metrics, runtime health, audit logs.

**Điều kiện cần:** Đã seed data (ít nhất 1 candidate, 1 job opening).

**Các bước:**

1. Mở http://localhost:3000 → đăng nhập `admin@vroomhr.com` / `VroomAdmin!2026`
2. Sau login, tự động vào **Dashboard & Metrics**
3. **Verify Recruitment Metrics:**
   - Queue Depth (số CV đang chờ xử lý)
   - Success Rate / Failure Rate
   - Avg Processing Time
   - Job Opening statuses (biểu đồ tròn: draft, open, closed, cancelled)
4. **Verify Runtime Health:**
   - Các service: Redis, PostgreSQL, MinIO, Gmail Worker
   - Status (Up/Down), Latency, Last Checked
5. **Verify Audit Log:**
   - Bảng log hoạt động gần đây (user, action, timestamp)
   - Ô tìm kiếm filter log

**Kỳ vọng:**
- Metric cards hiển thị số liệu thực (không phải 0 hoặc placeholder)
- Runtime health có ít nhất 3 service xanh (Up)
- Audit log có ít nhất 1 dòng ghi nhận login

**Ghi chú:**
- Nếu chưa seed, các số liệu có thể bằng 0 — đó là behavior đúng
- Audit log tự ghi khi user login, tạo employee, v.v.

---

### #2: Recruitment Inbox

**Mục tiêu:** Xem hộp thư tuyển dụng — nơi email từ ứng viên được AI phân loại.

**Điều kiện cần:**
- Đã seed emails (qua `seed_db.py` hoặc `seed_gmail.py`)
- Hoặc đã có Gmail connected + có email thực

**Các bước:**

1. Click **"Recruitment Inbox"** trên sidebar
2. **Verify các tab filter:**
   - All / Needs classification / Needs information / Ready for review / Resolved
3. Click vào từng tab — verify count badge thay đổi
4. Click vào 1 email bất kỳ → xem detail panel:
   - Nội dung email
   - AI classification (intent: Job Application, Partner, Event...)
   - Nút "Promote → Candidate" (nếu là job application)

**Kỳ vọng:**
- Danh sách email hiển thị (nếu có seed)
- Mỗi email có: subject, sender, date, AI classification badge
- Tab filter hoạt động, count badge chính xác

**Ghi chú:**
- Nếu chưa connect Gmail, inbox sẽ rỗng — đây là behavior đúng
- Có thể skip nếu chưa có Google OAuth

---

### #3: Candidates

**Mục tiêu:** Xem danh sách ứng viên, tìm kiếm, lọc, thao tác (reject/accept/assign).

**Điều kiện cần:** Đã seed candidates (seed_all.py tạo 55 candidates).

**Các bước:**

1. Click **"Candidates"** trên sidebar
2. **Verify danh sách:**
   - Avatar/name, email, skills (badge), status (badge màu)
   - Confidence score, ngày tạo
3. **Thử filter:**
   - Ô search: nhập "Nguyễn" → danh sách lọc realtime
   - Dropdown status: chọn "Interview Scheduled" → chỉ hiện candidates đang phỏng vấn
4. **Click vào 1 candidate** → xem detail:
   - Thông tin cá nhân (name, email, phone)
   - Skills (full list), Experience (work history), Education
   - CV documents (nếu có)
   - Interview schedule (nếu có)
5. **Thao tác (nếu muốn demo):**
   - **Reject:** click "Reject" → nhập lý do → confirm
   - **Archive:** click "Archive"
   - **Accept → Onboarding:** click "Accept → Onboarding" (tự tạo onboarding process)

**Kỳ vọng:**
- Danh sách có pagination (Page 1/3...)
- Search hoạt động với name, email, skills
- Status badge màu sắc phân biệt (xanh = accepted, đỏ = rejected, v.v.)
- Candidate detail hiển thị đủ các section

---

### #4: Job Openings

**Mục tiêu:** Xem danh sách vị trí tuyển dụng, tạo mới, mở/đóng tuyển.

**Điều kiện cần:** Đã seed job openings (seed_all.py tạo 12 openings).

**Các bước:**

1. Click **"Job Openings"** trên sidebar
2. **Verify danh sách:**
   - Title, Position, Target headcount
   - Status badge (Draft/Open/Closed/Cancelled)
   - Số candidate đang review
   - Progress bar (filled vs headcount)
3. **Thử filter:**
   - Tab: Total / Draft / Open / Closed / Cancelled
   - Search: nhập "Senior" → danh sách filter theo title
4. **Tạo mới Job Opening:**
   - Click **"Create job opening"**
   - Nhập title: _"Intern Frontend Developer"_
   - Chọn Position từ dropdown
   - Target headcount: `3`
   - Status: chọn "Draft" hoặc "Open now"
   - Description: _"Chương trình thực tập cho sinh viên năm cuối"_
   - Click **Save**
5. **Verify** Job Opening mới xuất hiện trong danh sách
6. **Mở tuyển (nếu tạo draft):** click nút "Open recruitment" → status chuyển thành Open

**Kỳ vọng:**
- Danh sách có pagination
- Filter tabs thay đổi danh sách chính xác
- Create form có đủ fields + validation
- Job Opening mới hiển thị ngay sau save

---

### #5: Interview Schedule

**Mục tiêu:** Xem lịch phỏng vấn, kiểm tra calendar conflicts.

**Điều kiện cần:** Đã seed interviews (seed_all.py tạo 50 interviews).

**Các bước:**

1. Click **"Interview Schedule"** trên sidebar
2. **Verify:**
   - Calendar selector (nếu Google Calendar connected)
   - Danh sách interviews sắp tới
   - Candidates to schedule / scheduled count
3. Nếu có Google Calendar:
   - Conflict resolution panel
   - Interview creation form

**Kỳ vọng:**
- Danh sách interview hiển thị (candidate name, round, time, status)
- Có thể xem chi tiết interview (participants, mode, meeting link)

**Ghi chú:**
- Interview creation yêu cầu Google Calendar connected (xem Gmail Channel)
- Nếu chưa có calendar, page vẫn render danh sách + thông báo cần connect

---

### #6: CV Review (Parse)

**Mục tiêu:** Xem hàng đợi parse CV, chỉnh sửa thông tin AI trích xuất.

**Điều kiện cần:** Có email với CV attachment đã được xử lý.

**Các bước:**

1. Click **"CV Review (Parse)"** trên sidebar
2. **Verify:**
   - Queue: danh sách CV đang chờ/đã parse
   - Mỗi item: candidate name, extract confidence, parsed fields
3. **Nếu có item:** click vào → xem parsed data
   - AI-extracted: name, email, phone, skills, experience, education
   - Nút "Submit correction" nếu cần sửa
   - Nút "Retry parse" nếu lỗi

**Kỳ vọng:**
- Hàng đợi hiển thị parsed candidates
- Parsed fields match với AI extraction

**Ghi chú:**
- Parse queue thường rỗng nếu chưa seed emails — đây là behavior đúng
- Có thể skip nếu không có seed emails

---

### #7: Recruitment Metrics

**Mục tiêu:** Xem thống kê tuyển dụng chi tiết.

**Các bước:**

1. Click **"Recruitment Metrics"** trên sidebar
2. **Verify:**
   - Queue depth (số documents đang chờ xử lý)
   - Success rate / Failure rate (24h gần nhất)
   - Avg processing time
   - Job Opening statuses (biểu đồ)

**Kỳ vọng:**
- Các số liệu cập nhật realtime
- Biểu đồ hiển thị phân bố job opening theo status

---

### #8: Onboarding Processes

**Mục tiêu:** Xem danh sách onboarding processes, theo dõi tiến độ.

**Điều kiện cần:** Đã seed onboarding (seed_all.py tạo 15 processes).

**Các bước:**

1. Click **"Onboarding Processes"** trên sidebar
2. **Verify danh sách:**
   - Employee name, email, employee code
   - Status badge (In Progress / Complete)
   - Progress: completed count / total count
3. **Click vào 1 process** → xem detail:
   - Checklist các task (Cập nhật thông tin cá nhân, Nộp giấy tờ...)
   - Task status (pending / done) + completed_by + completed_at
4. **Mark task done (nếu có task pending):**
   - Click checkbox hoặc nút "Mark done"
   - Task chuyển thành "done" + ghi nhận người thực hiện

**Kỳ vọng:**
- Danh sách process hiển thị đúng tiến độ
- Checklist hiển thị đủ tasks
- Khi task cuối được done → process complete + employee active

**Ghi chú:**
- Onboarding process tự động tạo khi candidate được accept
- Hoàn thành task cuối cùng sẽ kích hoạt employee (is_active = true)

---

### #9: Employee List

**Mục tiêu:** Xem danh sách nhân viên, lọc, tìm kiếm, tạo mới.

**Điều kiện cần:** Đã seed employees (seed_all.py tạo 55 employees).

**Các bước:**

1. Click **"Employee List"** trên sidebar
2. **Verify danh sách:**
   - Avatar, full name, email, department, position
   - Employee code, status (Active/Inactive badge)
3. **Thử filter:**
   - Search: nhập "Nguyễn" → danh sách lọc
   - Department filter: chọn "Phòng Kỹ Thuật"
   - Active/Inactive toggle
4. **Tạo mới Employee:**
   - Click **"Add Employee"**
   - Nhập: Full name = _"Lê Văn Test"_, Email = _"levan.test@vroom.vn"_
   - Chọn Department, Position
   - Start date: hôm nay
   - Click **Save**
5. **Verify** Employee mới xuất hiện trong danh sách
6. **Click vào 1 employee** → xem detail:
   - Personal info, contact, work info
   - Documents (nếu có)
   - Employee Account section (nếu đã tạo account)
   - Nút "Tạo tài khoản" (nếu chưa có account)

**Kỳ vọng:**
- Danh sách paginated (20 items/page)
- Search filter realtime
- Create form validation (email unique, required fields)
- Employee detail hiển thị đủ 3 tab: Info, Documents, Account

---

### #10: Employee Requests

**Mục tiêu:** Duyệt/từ chối yêu cầu của nhân viên (nghỉ phép, làm thêm).

**Điều kiện cần:** Đã seed employee requests (seed_all.py tạo 60 requests).

**Các bước:**

1. Click **"Employee Requests"** trên sidebar
2. **Verify danh sách yêu cầu đang chờ duyệt:**
   - Employee name, request type (Leave/Overtime)
   - Dates, reason, status (Submitted)
3. **Thử filter:**
   - Request type: Leave / Overtime
   - Status: Submitted / Approved / Rejected
   - Date range
4. **Approve 1 request:**
   - Click vào request → click "Approve"
   - Nhập review reason (optional) → confirm
   - Status chuyển thành "Approved"
5. **Reject 1 request:**
   - Click vào request → click "Reject"
   - Nhập reason (required) → confirm
   - Status chuyển thành "Rejected"

**Kỳ vọng:**
- Request queue hiển thị yêu cầu thực từ employee
- Approve/Reject flow hoạt động đúng
- Audit log ghi nhận hành động duyệt/từ chối

---

### #11: Attendance & Allowlist

**Mục tiêu:** Xem bảng chấm công, quản lý network allowlist.

**Điều kiện cần:** Đã seed attendance records.

**Các bước:**

1. Click **"Attendance & Allowlist"** trên sidebar
2. **Verify Attendance Records tab:**
   - Date range picker (start date → end date)
   - Danh sách records: employee name, check-in, check-out, status
   - Filter by employee, status (checked_in/completed)
3. **Thử filter:** chọn 1 employee cụ thể → records lọc theo employee
4. **Chuyển tab: Network Allowlist**
   - Danh sách CIDR được phép check-in
   - Nút "Add" để thêm CIDR mới
5. **Thêm CIDR (nếu muốn):**
   - Nhập `192.168.1.0/24` → Add
   - Verify CIDR xuất hiện trong danh sách

**Kỳ vọng:**
- Records hiển thị check-in/out thực tế
- Filter date range hoạt động
- Allowlist CRUD hoạt động (add/remove)

---

### #12: Payslips

**Mục tiêu:** Tạo phiếu lương draft, publish cho nhân viên.

**Điều kiện cần:** Đã seed payslips (seed_all.py tạo ~160 payslips).

**Các bước:**

1. Click **"Payslips"** trên sidebar (trong mục Payroll)
2. **Verify danh sách:**
   - Employee name, period, gross/net salary
   - Status badge (Draft / Published)
   - Filter: by employee, status, period
3. **Thử filter:** chọn status "Published" → chỉ hiện payslip đã phát hành
4. **Tạo mới Payslip Draft:**
   - Click **"Create payslip"**
   - Chọn Employee (VD: Nguyễn Minh Tuấn)
   - Period: tháng hiện tại (YYYY-MM)
   - Gross Salary: `25,000,000`
   - Deductions: `2,000,000`
   - Net Salary: `23,000,000`
   - Click **Save**
5. **Verify** payslip mới xuất hiện với status "Draft"
6. **Publish payslip:**
   - Click vào payslip draft → click "Publish"
   - Status chuyển thành "Published" + ghi nhận thời gian publish
   - Employee có thể thấy payslip này trên ESS

**Kỳ vọng:**
- Danh sách payslip đầy đủ (sau seed)
- Create form validation (unique employee+period)
- Draft không lộ cho employee
- Publish không thể undo

---

### #13: Knowledge Base

**Mục tiêu:** Quản lý tài liệu nội bộ — upload, xem, xoá.

**Các bước:**

1. Click **"Knowledge Base"** trên sidebar
2. **Verify:**
   - Danh sách tài liệu đã upload (nếu có)
   - Nút "Upload" để thêm tài liệu mới
3. **Upload tài liệu (nếu muốn):**
   - Click "Upload" → chọn 1 file PDF/Word từ máy
   - Nhập mô tả (optional)
   - Click Save
   - Verify document xuất hiện trong danh sách
4. **Xem tài liệu:**
   - Click vào tài liệu → download hoặc preview
   - Nút "Delete" (nếu cần xoá)

**Kỳ vọng:**
- File upload thành công
- Document list hiển thị đúng metadata (name, type, size, upload date)

---

### #14: Gmail Channel

**Mục tiêu:** Kết nối Google Workspace Gmail, cấu hình sync.

**Các bước:**

1. Click **"Gmail Channel"** trên sidebar
2. **Verify:**
   - Trạng thái kết nối Google Workspace
   - Nút "Connect Google Workspace" (nếu chưa kết nối)
   - Hoặc thông tin đã kết nối (connected email, calendar status...)
3. **Nếu đã kết nối:**
   - Calendar selector (chọn calendar cho interviews)
   - Sync status (last synced, emails in queue)
   - Nút "Sync now" (nếu cần)

**Kỳ vọng:**
- Page render rõ trạng thái kết nối
- Hướng dẫn kết nối nếu chưa có OAuth

**Ghi chú:**
- Yêu cầu: Google Workspace account + OAuth 2.0 credentials
- Có thể skip nếu chưa có Google OAuth config
- Nếu chưa kết nối → có thể demo UI "chưa kết nối" + hướng dẫn

---

### #15: AI & System Settings

**Mục tiêu:** Cấu hình AI, xem system health, audit log, quản lý users.

**Các bước:**

1. Click **"Settings"** trên sidebar
2. **Verify các tab settings:**
   - **System Health:** xem trạng thái runtime services (giống Dashboard)
   - **Audit Log:** xem log hoạt động (filterable)
   - **Access Whitelist:** quản lý danh sách email được phép truy cập
   - **Users & Roles:** danh sách user, role
   - **AI Provider:** cấu hình LLM provider (OpenAI, Anthropic...)
   - **AI Tool Config:** bật/tắt tools cho AI Assistant
3. **Nếu có quyền admin:**
   - Xem danh sách user với role (admin/user)
   - Bật/tắt AI tools cho assistant

**Kỳ vọng:**
- Tất cả tabs render đúng
- System health match với Dashboard
- Audit log filter theo action type
- User list hiển thị ít nhất admin user

---

### #16: AI Assistant (HR)

**Mục tiêu:** Chat với AI Assistant, verify human-in-the-loop (AI không tự động ghi dữ liệu).

**Điều kiện cần:** Có LLM provider key (OpenAI/Anthropic) đã cấu hình trong Settings.

**Các bước:**

1. Click **"AI Assistant"** trên sidebar
2. **Verify:**
   - Chat interface: input box + send button
   - Trạng thái "AI Assistant (HR)" — human-in-the-loop mode
3. **Gửi câu hỏi read-only:**
   - Nhập: _"Có bao nhiêu ứng viên đang ở trạng thái new?"_
   - Click Send
   - **Kỳ vọng:** AI trả lời dựa trên data thật (candidate count)
4. **Gửi câu hỏi write-action (nếu có thể):**
   - Nhập: _"Tạo một job opening mới cho Senior Rust Developer"_
   - **Kỳ vọng:** AI trả lời rằng cần HR confirm, không tự động ghi
   - Draft action panel xuất hiện với nút "Confirm" hoặc "Reject"
5. **Verify safety:**
   - Không có text "tự động lưu", "auto-confirm" trên page
   - Mọi hành động ghi dữ liệu đều cần HR confirm

**Kỳ vọng:**
- AI trả lời câu hỏi read-only từ database thật
- Draft action không tự động ghi — chỉ ghi sau HR confirm
- Nếu LLM provider chưa cấu hình → error message rõ ràng

**Ghi chú:**
- Nếu chưa có LLM key, test này sẽ fail — có thể skip hoặc config trước
- Cần restart backend sau khi config AI provider

---

## Phần 3: Employee Self-Service (ESS) Demo

> **Bước chuẩn bị:** HR cần tạo Employee Account trước (xem Bước 3 ở Phần 1). Sau đó login như employee và đổi mật khẩu.

### Employee Login Flow

1. Mở http://localhost:3000/login
2. Nhập email employee (VD: `employee.qa@vroom.example.com` hoặc email employee vừa tạo)
3. Nhập mật khẩu tạm thời
4. **Lần đầu login:** bắt buộc đổi mật khẩu
   - Nhập mật khẩu hiện tại
   - Nhập mật khẩu mới (`Dem0Emp!Pass`)
   - Xác nhận mật khẩu mới
   - Submit → tự động chuyển đến /employee/dashboard
5. **Các lần sau:** login bình thường → thẳng đến /employee

---

### #17: Employee Dashboard

**Mục tiêu:** Xem bảng cá nhân — greeting, các card chức năng.

**Các bước:**

1. Sau login → tự động vào Employee Dashboard
2. **Verify:**
   - Greeting: "Xin chào, {employee_name}!"
   - **6 cards chức năng:**
     - My Profile → xem/sửa thông tin cá nhân
     - My Documents → tài liệu của tôi
     - Attendance → chấm công
     - My Requests → yêu cầu của tôi
     - My Payslips → phiếu lương
     - AI Assistant → trợ lý AI

**Kỳ vọng:**
- Greeting hiển thị đúng tên employee
- 6 cards với icon + title + description
- Click card → navigate đến trang tương ứng

---

### #18: Attendance (ESS)

**Mục tiêu:** Check-in/Check-out, xem lịch sử chấm công.

**Các bước:**

1. Click **"Attendance"** card hoặc sidebar item
2. **Verify:**
   - Nút "Check-in" (nếu chưa check-in hôm nay)
   - Hoặc thông tin đã check-in (time, duration)
   - History: danh sách các ngày gần đây
3. **Check-in:**
   - Click "Check-in"
   - **Kỳ vọng:** success message + record hiển thị
   - (Nếu IP không trong allowlist → error message rõ ràng)
4. **Check-out (nếu đã check-in):**
   - Click "Check-out"
   - **Kỳ vọng:** success + tính toán duration
5. **Xem lịch sử:**
   - Tab monthly view hoặc recent days
   - Check-in/out time, status, source (Web/Mobile)

**Ghi chú:**
- Check-in yêu cầu IP trong network allowlist (config ở Settings)
- Nếu local dev, IP thường là 127.0.0.1 hoặc ::1

---

### #19: My Requests

**Mục tiêu:** Tạo yêu cầu nghỉ phép, xem trạng thái.

**Các bước:**

1. Click **"My Requests"** card hoặc sidebar item
2. **Verify:**
   - Danh sách yêu cầu đã gửi (nếu có)
   - Status badges: Submitted / Approved / Rejected
3. **Tạo yêu cầu nghỉ phép mới:**
   - Click "Create request" hoặc "New leave request"
   - Leave type: chọn "Annual"
   - Start date: 2 tuần sau
   - End date: start date + 2 ngày
   - Reason: _"Nghỉ phép năm — về quê thăm gia đình"_
   - Submit
4. **Verify** request mới xuất hiện với status "Submitted"
5. **Tạo yêu cầu trùng (để test LEAVE_OVERLAP):**
   - Tạo request khác cùng ngày
   - **Kỳ vọng:** error message "LEAVE_OVERLAP" — phát hiện trùng lịch

**Kỳ vọng:**
- Leave request tạo thành công
- LEAVE_OVERLAP error khi trùng ngày
- Request list hiển thị đúng trạng thái
- HR có thể approve/reject từ admin page

---

### #20: Payslips (ESS)

**Mục tiêu:** Xem phiếu lương đã publish (draft không lộ).

**Điều kiện cần:** Đã seed payslips cho employee này.

**Các bước:**

1. Click **"My Payslips"** card hoặc sidebar item
2. **Verify:**
   - Danh sách phiếu lương "Danh sách phiếu lương"
   - Mỗi payslip: period (tháng), gross/net salary, status
   - Status badge: "Đã phát hành" (Published)
3. **Safety check:**
   - **Không** được thấy bất kỳ payslip nào có badge "Bản nháp" / "Draft"
   - Employee chỉ thấy payslip đã publish

**Kỳ vọng:**
- Danh sách payslip hiển thị (nếu có seed)
- Tất cả payslip đều published
- Không leak draft payslip

---

### #21: AI Assistant (Employee)

**Mục tiêu:** Chat với AI Assistant ở chế độ employee (read-only).

**Điều kiện cần:** Có LLM provider key đã cấu hình.

**Các bước:**

1. Click **"AI Assistant"** card hoặc sidebar item
2. **Verify:**
   - Chat interface (giống HR assistant)
   - Mode: "AI Assistant (Employee)" — read-only
3. **Gửi câu hỏi:**
   - Nhập: _"Tôi còn bao nhiêu ngày phép năm?"_
   - **Kỳ vọng:** AI trả lời dựa trên leave balance thực tế
4. **Verify safety:**
   - Employee assistant không được phép ghi dữ liệu
   - Nếu yêu cầu write action → AI từ chối hoặc hướng dẫn tạo request

**Kỳ vọng:**
- AI trả lời từ database
- Read-only mode — không có nút confirm action

---

## Phần 4: Edge Cases

### EC1: Employee không access admin page

**Mục tiêu:** Employee không thể xem trang admin (redirect hoặc forbidden).

**Các bước:**

1. Login employee → ở trang /employee/dashboard
2. Trên URL, nhập `http://localhost:3000/dashboard` (admin page)
3. **Kỳ vọng:**
   - Redirect về `/employee` hoặc `/login`
   - Hoặc hiển thị error 403 / "Access Denied"

---

### EC2: Không auth → redirect /login

**Mục tiêu:** Trang protected không cho phép truy cập nếu chưa login.

**Các bước:**

1. Mở tab ẩn danh (incognito)
2. Vào http://localhost:3000/dashboard
3. **Kỳ vọng:** tự động redirect về http://localhost:3000/login

---

### EC3: Logout → redirect /login

**Mục tiêu:** Logout đưa user về login page.

**Các bước:**

1. Login admin bất kỳ
2. Click **"Log out"** button (góc trên bên phải)
3. **Kỳ vọng:**
   - Redirect về /login
   - Nếu vào lại /dashboard → redirect về /login (session đã clear)

---

## Phần 5: Phụ lục

### A. API Endpoints hữu ích

#### Identity & Auth

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/auth/login` | Login (body: `{email, password}`) |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/auth/setup-status` | Kiểm tra setup complete? |
| POST | `/api/auth/change-password` | Đổi mật khẩu |

#### Recruitment

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/recruitment/candidates` | Danh sách candidates (có filter) |
| GET | `/api/recruitment/candidates/{id}` | Candidate detail |
| POST | `/api/recruitment/candidates/{id}/accept` | Accept candidate |
| POST | `/api/recruitment/candidates/{id}/reject` | Reject candidate |
| GET | `/api/recruitment/job-openings` | Danh sách job openings |
| POST | `/api/recruitment/job-openings` | Tạo job opening |
| POST | `/api/recruitment/job-openings/{id}/open` | Mở tuyển |
| GET | `/api/recruitment/inbox` | Recruitment inbox |
| GET | `/api/recruitment/metrics` | Recruitment metrics |

#### Employees

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/employees` | Danh sách employees |
| POST | `/api/employees` | Tạo employee mới |
| GET | `/api/employees/{id}` | Employee detail |
| POST | `/api/employees/{id}/account` | Tạo employee account |
| POST | `/api/employees/promote` | Promote candidate → employee |
| GET | `/api/departments` | Danh sách departments |
| POST | `/api/departments` | Tạo department |
| GET | `/api/positions` | Danh sách positions |
| POST | `/api/positions` | Tạo position |

#### Payroll

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/admin/payslips` | Danh sách payslips (admin) |
| POST | `/api/admin/payslips` | Tạo payslip draft |
| POST | `/api/admin/payslips/{id}/publish` | Publish payslip |
| GET | `/api/payslips/me` | Payslip của employee (ESS) |

#### Attendance

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/attendance/records` | Danh sách records (admin) |
| POST | `/api/attendance/me/check-in` | Check-in (ESS) |
| POST | `/api/attendance/me/check-out` | Check-out (ESS) |
| GET | `/api/attendance/me/today` | Record hôm nay (ESS) |

#### Employee Requests

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/admin/employee-requests` | Review queue (admin) |
| POST | `/api/admin/employee-requests/{id}/approve` | Approve request |
| POST | `/api/admin/employee-requests/{id}/reject` | Reject request |
| POST | `/api/employee-requests/me/leave` | Tạo leave (ESS) |
| POST | `/api/employee-requests/me/overtime` | Tạo overtime (ESS) |

#### Onboarding

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/onboarding/processes` | Danh sách processes |
| GET | `/api/onboarding/processes/{id}` | Process detail |
| PATCH | `/api/onboarding/tasks/{id}` | Mark task done |

### B. Cách reset mật khẩu employee

Nếu employee quên mật khẩu hoặc cần reset:

```bash
cd backend && python3 -c "
from src.modules.identity.infrastructure.password_utils import hash_password
print(hash_password('NewPassword!2026'))
"
# Copy hash và chạy:
docker exec vroom-postgres psql -U postgres -d vroom_hr \
  -c "UPDATE users SET password_hash = 'PASTE_HASH', must_change_password = true \
      WHERE email = 'employee.qa@vroom.example.com';"
```

Hoặc xoá account employee và tạo lại từ UI:

```bash
# Xoá account (idempotent)
curl -X DELETE "http://localhost:8000/api/employees/{EMPLOYEE_ID}/account" \
  -H "Cookie: access_token=YOUR_ADMIN_TOKEN"
# Sau đó tạo lại từ UI: Employees → detail → "Tạo tài khoản"
```

### C. Tài khoản test

| Vai trò | Email | Mật khẩu | Ghi chú |
|---|---|---|---|
| **Admin (auto-seed)** | `admin@vroomhr.com` | `VroomAdmin!2026` | Admin chính của hệ thống |
| **Admin (seed_all)** | `hr@vroom.com` | `admin123` | Tạo bởi seed_all.py |
| **Employee demo** | Cần tạo | temp password | Xem Bước 3 Phần 1 |
| **HR QA (smoke test)** | `hr.qa@vroom.example.com` | `VroomQA!148#2026` | Dùng trong CI |

### D. Troubleshooting

**Problem:** `docker compose ps` thấy service không running
**Solution:** `docker compose up -d`

**Problem:** Seed data không hiển thị trên UI
**Solution:** Kiểm tra `AUTH_AUTO_SEED_SAMPLE_DATA=true` trong backend/.env

**Problem:** Employee login báo lỗi "Invalid credentials"
**Solution:** Employee chưa có account → tạo account từ UI hoặc API (xem Bước 3)

**Problem:** AI Assistant không trả lời
**Solution:** Chưa config LLM provider key trong Settings → AI Provider

**Problem:** Gmail Channel hiển thị "not connected"
**Solution:** Yêu cầu Google OAuth 2.0 credentials — có thể skip demo

---

> **Kết thúc kịch bản demo.**  
> Toàn bộ 21 mục demo + 3 edge cases đã được kiểm tra.  
> Hệ thống Vroom HR hoạt động với đầy đủ: HR Admin (16 mục) + Employee ESS (5 mục) + Edge Cases.
