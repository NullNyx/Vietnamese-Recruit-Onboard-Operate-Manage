# Kế hoạch Triển khai Hệ thống Chấm Công & Tính Lương

## Tổng quan

Dựa trên `cham-cong-luong.md`, triển khai thành 4 giai đoạn với 14 tuần tổng cộng.

**Module hiện tại**: Attendance (trống, cần xây dựng từ đầu)
**Module mới**: Payroll (chưa tồn tại, cần tạo mới)

---

## Giai đoạn 1 — MVP (4 tuần)

### Tuần 1: Database & Domain

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 1.1 | Tạo migration: attendance_records, work_shifts, overtime_config | ✅ | - |
| 1.2 | Tạo migration: payroll_salary, payroll_allowances | ✅ | - |
| 1.3 | Domain entities: AttendanceRecord, WorkShift, OvertimeConfig | ✅ | - |
| 1.4 | Domain entities: SalaryConfig, Allowance, PayrollRecord | ✅ | - |
| 1.5 | Container + DI cho attendance module | ✅ | - |

### Tuần 2: Check-in API

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 1.6 | POST /api/v1/attendance/checkin | ✅ | - |
| 1.7 | POST /api/v1/attendance/checkout | ✅ | - |
| 1.8 | GET /api/v1/attendance/history | ✅ | - |
| 1.9 | HR: PUT /api/v1/attendance/records/{id} (sửa thủ công) | ✅ | - |
| 1.10 | Audit log cho mọi thay đổi | ✅ | - |

### Tuần 3: Tính công cơ bản

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 1.11 | Tính work_hours, late_minutes, early_minutes | ✅ | - |
| 1.12 | Service tính công tháng | ✅ | - |
| 1.13 | Export Excel bảng công | ✅ | - |
| 1.14 | Settings: Fixed hours config | ✅ | ✅ |

### Tuần 4: Tính lương cơ bản

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 1.15 | Công thức Gross → Net (BHXH 10.5%, thuế TNCN) | ✅ | - |
| 1.16 | GET /api/v1/payroll/calculate | ✅ | - |
| 1.17 | Employee: xem phiếu lương | ✅ | ✅ |
| 1.18 | Export Excel bảng lương | ✅ | - |
| 1.19 | Đăng ký router vào main.py | ✅ | - |

**MVP hoàn chỉnh**: Web Check-in + Fixed hours + Tính công + Gross → Net

---

## Giai đoạn 2 — Ca & OT (4 tuần)

### Tuần 5-6: Quản lý ca (Shift)

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 2.1 | CRUD WorkShift | ✅ | ✅ |
| 2.2 | Phân ca cho employee (theo tuần/tháng/nhóm) | ✅ | ✅ |
| 2.3 | Check-in theo ca | ✅ | - |
| 2.4 | Tính giờ theo ca | ✅ | - |

### Tuần 7: Overtime

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 2.5 | POST /api/v1/attendance/overtime (đăng ký OT) | ✅ | ✅ |
| 2.6 | PUT /api/v1/attendance/overtime/{id}/approve (duyệt) | ✅ | ✅ |
| 2.7 | Tự động tính OT: 1.5x T2-T6, 2x T7-CN, 3x lễ | ✅ | - |
| 2.8 | Cấu hình OT max/ngày, max/tháng | ✅ | ✅ |

### Tuần 8: Ngày nghỉ & QR

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 2.9 | Load lịch lễ VN (Tết âm lịch) | ✅ | ✅ |
| 2.10 | QR code generation | ✅ | ✅ |
| 2.11 | GET /api/v1/attendance/qr/{qr_code_id} | ✅ | - |
| 2.12 | Alert/notification | ✅ | ✅ |

---

## Giai đoạn 3 — Mở rộng (3 tuần)

### Tuần 9-10: Flexible & Exception

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 3.1 | Flexible hours config | ✅ | ✅ |
| 3.2 | Tính giờ flexible (đủ 8h/ngày) | ✅ | - |
| 3.3 | POST /api/v1/attendance/exception (xin ngoại lệ) | ✅ | ✅ |
| 3.4 | Duyệt exception | ✅ | ✅ |
| 3.5 | Hybrid model (Fixed + Flexible theo phòng ban) | ✅ | ✅ |

### Tuần 11: Dashboard & Manager

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 3.6 | HR Dashboard widget | ✅ | ✅ |
| 3.7 | Manager: xem attendance team | ✅ | ✅ |
| 3.8 | Manager duyệt OT | ✅ | ✅ |
| 3.9 | IP Whitelist config | ✅ | ✅ |

---

## Giai đoạn 4 — Nâng cao (3 tuần)

### Tuần 12-13: Device Integration

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 4.1 | Device management (CRUD) | ✅ | ✅ |
| 4.2 | POST /api/v1/attendance/device-checkin | ✅ | - |
| 4.3 | Face ID: DeepFace integration | ✅ | ✅ |

### Tuần 14: Hoàn thiện

| Task | Mô tả | Backend | Frontend |
|------|-------|---------|----------|
| 4.4 | Payroll: 2 lần/tháng | ✅ | ✅ |
| 4.5 | PDF phiếu lương | ✅ | - |
| 4.6 | Báo cáo nâng cao + biểu đồ | ✅ | ✅ |

---

## Câu hỏi cần xác nhận trước Giai đoạn 1

| # | Câu hỏi | Ảnh hưởng |
|---|---------|-----------|
| 1 | Giai đoạn 1 cần ca (Shift) ngay không? | Nếu có → gộp vào tuần 2-3 |
| 2 | Device integration có cần trong 3 tháng đầu? | Nếu không → bỏ qua Giai đoạn 4 |
| 3 | Quên check-in: HR sửa thẳng hay cần employee xin → HR duyệt? | Workflow khác nhau |
| 4 | OT: tự động tính hay bắt buộc đăng ký trước? | Logic khác nhau |
| 5 | Công ty dùng Gross hay Net? | Công thức tính |
| 6 | Trả lương 1 lần hay 2 lần / tháng? | Chu kỳ payroll |
| 7 | Đi muộn / về sớm có trừ lương không? | Logic tính |

---

## Thứ tự ưu tiên triển khai

```
Phase 1 (4 tuần)
├── Task 1.1-1.5   ← Bắt đầu từ đây (DB + Domain)
├── Task 1.6-1.10  ← Check-in API
├── Task 1.11-1.14 ← Tính công + Settings
├── Task 1.15-1.19 ← Tính lương cơ bản
└── Register router → MVP DONE

Phase 2 (4 tuần)
├── Task 2.1-2.4   ← Ca/Shift
├── Task 2.5-2.8   ← OT
└── Task 2.9-2.12  ← Ngày nghỉ + QR

Phase 3 (3 tuần)
├── Task 3.1-3.5   ← Flexible + Exception
└── Task 3.6-3.9   ← Dashboard + Manager

Phase 4 (3 tuần)
├── Task 4.1-4.3   ← Device + Face ID
└── Task 4.4-4.6   ← Hoàn thiện
```

---

## Ghi chú

- Module `attendance` đã tồn tại trong `backend/src/modules/attendance/` nhưng trống (chưa có file)
- Module `payroll` chưa tồn tại → tạo mới theo cấu trúc module như `employee`, `onboarding`
- Frontend pages cần tạo: `/hr/attendance`, `/hr/payroll`, `/employee/attendance`, `/manager/attendance`
- Theo ADRs, mỗi module cần có: `api/router.py`, `application/*_service.py`, `domain/entities.py`, `infrastructure/*_repository.py`, `container.py`

---

*File này mapping từng task trong `cham-cong-luong.md` thành work items cụ thể.*
*Version: 1.0 · Created: $(date +%Y-%m-%d)*

---

## Chi tiết Triển khai Frontend cho HR

### Tạo trang Settings → Chấm công

```
frontend/src/app/(dashboard)/settings/
├── attendance/
│   ├── page.tsx              # Redirect到 attendance/methods
│   ├── methods/
│   │   └── page.tsx          # Settings → Phương thức chấm công
│   ├── shifts/
│   │   └── page.tsx          # Settings → Quản lý ca
│   ├── work-model/
│   │   └── page.tsx          # Settings → Mô hình giờ làm
│   ├── overtime/
│   │   └── page.tsx          # Settings → OT
│   ├── holidays/
│   │   └── page.tsx          # Settings → Ngày nghỉ
│   ├── qr/
│   │   └── page.tsx          # Settings → QR Check-in
│   └── devices/
│       └── page.tsx          # Settings → Devices
├── payroll/
│   └── page.tsx              # Settings → Lương & Phụ cấp
```

### Pages chi tiết

#### 1. Settings → Phương thức chấm công (`/settings/attendance/methods`)

| Component | Mô tả |
|-----------|-------|
| MethodToggle | Switch bật/tắt Web/QR/Device |
| IPWhitelistTable | Danh sách IP được phép check-in |
| QRConfig | Config QR reset theo ca/ngày |
| DeviceList | Danh sách thiết bị kết nối |

#### 2. Settings → Quản lý ca (`/settings/attendance/shifts`)

| Component | Mô tả |
|-----------|-------|
| ShiftTable | CRUD ca làm việc |
| ShiftForm | Form tạo/sửa ca |
| EmployeeShiftAssign | Phân ca cho nhân viên |
| ShiftRotation | Cấu hình phân ca xoay vòng |

#### 3. Settings → Mô hình giờ làm (`/settings/attendance/work-model`)

| Component | Mô tả |
|-----------|-------|
| WorkModelSelect | Chọn Fixed/Shift/Flexible/Hybrid |
| FixedConfig | Form cấu hình giờ cố định |
| FlexibleConfig | Form cấu hình giờ linh hoạt |
| HybridConfig | Chọn phòng ban dùng mỗi mô hình |

#### 4. Settings → OT (`/settings/attendance/overtime`)

| Component | Mô tả |
|-----------|-------|
| OTRateTable | Tỷ lệ OT (1.5x/2x/3x) |
| OTLimitConfig | Max giờ/ngày, max giờ/tháng |
| OTApprovalFlow | Cấu hình người duyệt OT |

#### 5. Settings → Ngày nghỉ (`/settings/attendance/holidays`)

| Component | Mô tả |
|-----------|-------|
| HolidayCalendar | Lịch lễ VN (âm lịch) |
| CompanyHolidayList | Ngày nghỉ công ty |
| WeekendConfig | Chọn T7/CN nghỉ |

#### 6. Settings → QR Check-in (`/settings/attendance/qr`)

| Component | Mô tả |
|-----------|-------|
| QRGenerator | Tạo QR code |
| QRPreview | Xem trước QR |
| QRResetConfig | Cấu hình reset QR |

#### 7. Settings → Devices (`/settings/attendance/devices`)

| Component | Mô tả |
|-----------|-------|
| DeviceTable | Danh sách thiết bị |
| DeviceForm | Form thêm/sửa thiết bị |
| DeviceStatus | Trạng thái online/offline |

---

## Frontend cho Employee

```
frontend/src/app/(employee)/employee/
├── attendance/
│   ├── page.tsx              # Trang chủ chấm công
│   ├── checkin-button.tsx    # Nút Check-in/Check-out
│   ├── history/
│   │   └── page.tsx          # Lịch sử chấm công
│   └── shift/
│       └── page.tsx          # Xem ca hôm nay
├── payroll/
│   ├── page.tsx              # Phiếu lương
│   └── history/
│       └── page.tsx          # Lịch sử phiếu lương
```

---

## Frontend cho Manager

```
frontend/src/app/(dashboard)/
├── attendance/
│   ├── page.tsx              # Dashboard attendance team
│   ├── team/
│   │   └── page.tsx          # Xem attendance team
│   └── overtime/
│       └── page.tsx          # Duyệt OT
```

---

*Version: 1.0 · Updated: $(date +%Y-%m-%d)*

---

## Phần để Test MVP (đồng thời Frontend + Backend)

### Bước 1: Xác định API Contract

| Endpoint | Method | Request | Response | Dùng bởi |
|----------|--------|---------|----------|----------|
| `/api/v1/attendance/checkin` | POST | `{employee_id, timestamp, ip_address}` | `{status, checkin_time}` | Employee |
| `/api/v1/attendance/checkout` | POST | `{employee_id, timestamp}` | `{status, checkout_time, total_hours}` | Employee |
| `/api/v1/attendance/history` | GET | `?employee_id=&month=&year=` | `[{date, checkin, checkout, hours, status}]` | Employee |
| `/api/v1/attendance/records` | GET | `?month=&year=&department=` | `[{employee, date, checkin, checkout, hours}]` | HR |
| `/api/v1/attendance/records/{id}` | PUT | `{checkin_time, checkout_time}` | `{id, updated}` | HR |
| `/api/v1/attendance/settings/fixed` | GET/POST | `{start_time, end_time, break_start, break_end}` | `{settings}` | HR |
| `/api/v1/payroll/calculate` | POST | `{employee_id, month, year}` | `{gross, bhxh, bhyt, bhtn, tax, net}` | HR |
| `/api/v1/payroll/payslip/{employee_id}` | GET | `?month=&year=` | `{employee, salary, deductions, net}` | Employee |

### Bước 2: Frontend API Hooks cần tạo

```
frontend/src/hooks/queries/
├── use-attendance.ts       # GET history, GET records
├── use-checkin.ts          # POST checkin/checkout
├── use-attendance-settings.ts  # GET/POST settings
└── use-payroll.ts          # GET calculate, GET payslip

frontend/src/hooks/mutations/
├── use-checkin-mutation.ts # Check-in/out mutations
└── use-attendance-settings-mutation.ts
```

### Bước 3: Seed Data cho Test

| Table | Test Data |
|-------|-----------|
| employees | 5 employee mẫu |
| departments | 2 phòng ban (IT, Sales) |
| work_shifts | 3 ca (Sáng, Chiều, Cả ngày) |
| attendance_settings | Fixed config mẫu |
| salary_config | Gross 15,000,000 VND |

### Bước 4: Test Cases

#### Backend Unit Tests

| Test | Mô tả |
|------|-------|
| `test_checkin_creates_record` | Check-in tạo attendance record |
| `test_checkout_calculates_hours` | Check-out tính đúng giờ làm |
| `test_calculate_overtime_weekday` | OT ngày thường = 1.5x |
| `test_calculate_overtime_weekend` | OT cuối tuần = 2x |
| `test_calculate_overtime_holiday` | OT lễ = 3x |
| `test_gross_to_net_calculation` | Gross 15M → Net đúng công thức |
| `test_late_minutes_calculation` | Đi muộn tính đúng phút |

#### Frontend E2E Tests (Playwright/Vitest)

| Test | Mô tả |
|------|-------|
| `test_employee_checkin_flow` | Login → Check-in → Xem history |
| `test_hr_configure_fixed_hours` | Login → Settings → Set giờ cố định |
| `test_employee_view_payslip` | Login → Payroll → Xem phiếu lương |

### Bước 5: Docker Dev Environment

```yaml
# docker-compose.dev.yml cần có:
services:
  db:
    image: postgres:15
    ports:
      - "5432:5432"
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

---

## Checklist Test MVP

### Trước khi bắt đầu Phase 1

- [ ] Xác nhận 7 câu hỏi trong phần "Câu hỏi cần xác nhận"
- [ ] Dev environment chạy được (docker compose up)
- [ ] Database migration chạy được (alembic upgrade)
- [ ] Seed data chạy được

### Sau khi xây dựng xong Phase 1

- [ ] Backend: Tất cả API endpoints respond đúng
- [ ] Frontend: Tất cả pages render không lỗi
- [ ] Integration: Employee check-in → HR thấy record
- [ ] Integration: Tính công → Export Excel đúng
- [ ] Integration: Tính lương → Xem phiếu lương đúng
- [ ] Unit tests pass ≥ 80%
- [ ] E2E tests pass

---

*Version: 1.1 · Updated: $(date +%Y-%m-%d)*
