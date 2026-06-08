# PRD — Employee Self-Service Read-First (Task 5)

## Yêu cầu chức năng này giải quyết vấn đề gì?

Hiện tại hệ thống Vroom HR chỉ có **một bề mặt duy nhất: HR Admin**. HR quản lý tất cả — tuyển dụng, nhân viên, email, onboarding. Nhân viên (Employee) **không có cách nào** tự xem thông tin của mình mà phải hỏi HR.

Task 5 mở **bề mặt thứ hai: Employee Self-Service (ESS)** — nơi nhân viên đăng nhập bằng tài khoản công ty và tự phục vụ các nhu cầu cơ bản.

---

## Vận hành thực tế — Nhân viên dùng như thế nào?

### Bước 1: HR tạo nhân viên

```
HR vào /employees → tạo nhân viên mới "Nguyễn Thị Anh" (email: anh@vroom.vn)
→ Hệ thống tạo Employee record (is_active=true)
```

Lúc này trong database có:
- **User record**: email=anh@vroom.vn, role=user, linked employee_id=xxx
- **Employee record**: full_name="Nguyễn Thị Anh", department=People Ops, position=HR Generalist, phone=0901xxxx, address="123 Lê Lợi, Q1"

### Bước 2: Nhân viên đăng nhập

```
Anh mở app → Google OAuth → email anh@vroom.vn
→ Hệ thống check: domain vroom.vn có trong Organization allowed_domains? ✅
→ Hệ thống check: email này có link với Employee record nào? ✅ (is_active=true)
→ Tạo JWT token chứa: user_id + employee_id
→ Redirect vào Employee Self-Service surface
```

**Điểm mấu chốt:** JWT chứa `employee_id` — đây là "chìa khóa" để hệ thống biết "ai đang đăng nhập" và "cho phép xem gì".

### Bước 2b: Auto-redirect theo role (CẦN THÊM)

Sau khi Google OAuth callback, backend redirect về `http://localhost:3000`. Vấn đề: **cả admin lẫn employee đều landing trang admin dashboard**.

**Cần thêm logic redirect:**

```
After login → GET /api/auth/me → check role:
  - role=admin → stays at "/" (admin dashboard)
  - role=user + employee_id exists → redirect to "/employee/dashboard"
```

Cách triển khai: thêm root `page.tsx` hoặc sửa `(dashboard)/page.tsx` để auto-redirect employee.

### Bước 3: Anh xem Dashboard

```
/employee/dashboard
├── Quick link "Hồ sơ cá nhân" → /employee/profile
├── Quick link "Tài liệu" → /employee/documents
└── AI Assistant hint (chưa live)
```

Dashboard hiện 2 card — click vào dẫn tới trang tương ứng. Nav bar trên đầu hiển thị "Vroom ESS" với menu: Hồ sơ → Thông tin, Tài liệu.

**KHÔNG** hiện mục "Chấm công" hay "Lương" vì chưa implement.

### Bước 4: Anh xem hồ sơ cá nhân

```
/employee/profile
├── Card "Thông tin cơ bản": mã NV NV-003, ngày sinh, giới tính
├── Card "Thông tin công việc": ngày bắt đầu, loại hợp đồng, CCCD (mask ****1234), mã thuế (mask ****5678)
└── Card "Thông tin liên hệ": form chỉnh sửa phone + address
```

Anh thấy thông tin cá nhân. CCCD và mã thuế bị mask (ẩn bớt, chỉ hiện 4 số cuối) vì là thông tin nhạy cảm.

### Bước 5: Anh cập nhật số điện thoại

```
Anh sửa phone từ "0901000001" thành "0912345678"
→ Click "Lưu thay đổi"
→ Frontend gọi: PUT /api/employees/{anh_id}
   Body: { "phone": "0912345678" }
→ Backend kiểm tra:
   1. JWT employee_id == URL employee_id? ✅ (cùng một người)
   2. Fields được phép sửa: chỉ phone, address? ✅ (chỉ gửi phone)
   3. Gọi EmployeeService.update_employee()
→ Trả về 200 OK với dữ liệu mới
```

**Nếu Anh thử sửa trường khác** (ví dụ gửi thêm `"full_name": "Hack"`):
```
→ Backend kiểm tra: full_name không trong danh sách cho phép {phone, address}
→ Trả về 403: "Employees can only update phone and address"
→ Anh không sửa được
```

### Bước 6: Anh xem tài liệu cá nhân

```
/employee/documents
├── Table: tên file | loại | kích thước | ngày upload | nút tải
├── CCCD_Nguyen_Thi_Anh.pdf  | CCCD/CMND   | 239.3 KB | 05/06/2026 | ⬇
├── Hop_dong_lao_dong.pdf    | Hợp đồng    | 507.8 KB | 05/06/2026 | ⬇
└── Bang_dai_hoc.pdf         | Bằng cấp    | 371.1 KB | 05/06/2026 | ⬇
```

Anh thấy danh sách tài liệu HR đã upload. Click nút ⬇ để tải file.

### Bước 7: Anh thử xem tài liệu của người khác

```
Anh mở DevTools → sửa URL:
GET /api/employees/{B_id}/documents    ← B_id là employee khác

→ Backend kiểm tra:
   1. JWT employee_id (của Anh) != URL employee_id (của B)?
   2. Trả về 403: "Access denied: cannot access another employee's data"
→ Anh bị chặn, không thấy dữ liệu
```

Tương tự với download document:
```
GET /api/documents/{doc_of_B}/download

→ Backend check: document.employee_id (thuộc B) != current_user.employee_id (của Anh)?
→ Trả về 403
→ Anh không tải được
```

---

## Tóm tắt flow vận hành

```
┌─────────────────────────────────────────────────────────────────┐
│                    HR ADMIN (role=admin)                         │
│                                                                 │
│  /employees → tạo/sửa/xóa nhân viên (toàn quyền)               │
│  /employees/{id}/documents → upload tài liệu cho nhân viên      │
│  xem được dữ liệu TẤT CẢ employee                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Tạo Employee record
                    (is_active=true)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               EMPLOYEE SELF-SERVICE (role=user)                 │
│                                                                 │
│  /employee/dashboard → xem tổng quan                            │
│  /employee/profile → xem hồ sơ + sửa phone/address              │
│  /employee/documents → xem + tải tài liệu của MÌNH              │
│                                                                 │
│  ❌ Không xem được dữ liệu employee khác                        │
│  ❌ Không sửa được trường ngoài phone/address                    │
│  ❌ Không thấy nav Attendance/Payroll (chưa live)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phân biệt 2 role trong hệ thống

| | HR Admin | Employee |
|---|---|---|
| **JWT role** | `admin` | `user` |
| **JWT employee_id** | `null` | có giá trị |
| **Tạo nhân viên** | ✅ | ❌ |
| **Xem tất cả employee** | ✅ | ❌ (chỉ của mình) |
| **Sửa employee** | ✅ (tất cả field) | ⚠️ (chỉ phone + address) |
| **Upload document** | ✅ | ❌ (HR upload cho employee) |
| **Xem document** | ✅ (tất cả) | ⚠️ (chỉ document của mình) |
| **Download document** | ✅ (tất cả) | ⚠️ (chỉ document của mình) |
| **Nav hiện attendance** | ✅ | ❌ (ẩn, chưa live) |
| **Nav hiện payroll** | ✅ | ❌ (ẩn, chưa live) |
| **Sau login landing** | `/` (admin dashboard) | `/employee/dashboard` (CẦN THÊM redirect) |

---

## Scope

### In-scope

| Phân vùng | Chi tiết |
|-----------|----------|
| **Backend authz** | Ownership boundary: Employee chỉ xem/sửa profile và documents của mình |
| **Self-edit restriction** | `PUT /api/employees/{id}` chỉ cho phép employee sửa `phone` và `address` |
| **Frontend nav** | Ẩn Attendance/Payroll khỏi `essNavConfig`, EmployeeSidebar |
| **Post-login redirect** | Auto-redirect employee sang `/employee/dashboard` sau OAuth callback |
| **Seed/demo** | Thêm `EmployeeDocument` sample cho employee demo |
| **Tests** | Authz boundary tests, cross-employee access blocked |

### Out-of-scope

- Attendance / Leave / Overtime
- Payroll self-service
- Approval workflows
- Onboarding runtime wiring
- AI Assistant
- HR admin employee CRUD (ngoài giữ contract nhất quán)

---

## Acceptance Criteria

| # | Điều kiện | Verify bằng |
|---|-----------|-------------|
| 1 | Chỉ active Employees (`is_active=true`) truy cập được ESS | Test: inactive employee → 403 |
| 2 | Active Employee đăng nhập qua allowed domain → vào được ESS | Test: login flow |
| 3 | `/employee/dashboard`, `/employee/profile`, `/employee/documents` hoạt động E2E | Test: API call succeeds |
| 4 | Employee chỉ self-edit được **phone** và **address** | Test: gửi `full_name` → 403 |
| 5 | Employee **không thể** xem/sửa profile employee khác | Test: đổi employee_id → 403 |
| 6 | Employee **không thể** xem/tải document employee khác | Test: lấy doc_id khác → 403 |
| 7 | Employee nav **không hiển thị** Attendance/Payroll | Check: essNavConfig không có group đó |
| 8 | Employee login → **auto redirect** sang `/employee/dashboard` | Check: không landing admin dashboard |
| 9 | Có seed: 1 active Employee + sample documents | Check: demo_data seed thành công |
| 10 | Tests pass cho ownership/authz boundary | `pytest test_self_service_authz.py` |

---

## Output cần đạt

- Employee-facing UI đủ dùng cho active Employees
- Ownership-based authorization được chốt cho profile/documents endpoints
- Employee nav phản ánh đúng những gì đang live
- Post-login redirect đúng theo role (admin → `/`, employee → `/employee/dashboard`)
- Demo local có sẵn 1 active Employee + sample documents
- Có test bảo vệ boundary giữa Employee và dữ liệu của employee khác
